from __future__ import annotations
import importlib.metadata, math, os, re, uuid
from typing import Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

RUNTIME_ID="sc-runtime-spark"
ADAPTER_ID="adapter:sc-runtime-spark"
PROVIDER_VERSION="1.0.0"
SPARK_VERSION="4.2.0"
SCALA_BINARY_VERSION="2.13"
JVM_SUPPORTED=("17","21")
OPERATIONS=("spark_runtime_info","distributed_sum","distributed_map_affine","dataframe_group_aggregate","dataframe_filter_project","partition_summary")
MAX_NUMERIC_VALUES=10000
MAX_ROWS=5000
MAX_COLUMNS=64
MAX_PARTITIONS=8
DEFAULT_PARTITIONS=2
ALLOWED_AGGREGATES={"sum","avg","count","min","max"}
ALLOWED_FILTER_OPS={"eq","neq","gt","gte","lt","lte"}
app=FastAPI(title="Sustainable Catalyst Spark Runtime", version=PROVIDER_VERSION)
_spark=None

class FilterSpec(BaseModel):
    column: str = Field(min_length=1,max_length=128)
    op: str = Field(min_length=1,max_length=8)
    value: str|int|float|bool|None=None

class ExecuteRequest(BaseModel):
    operation: str
    values: list[float]=Field(default_factory=list)
    rows: list[dict[str,Any]]=Field(default_factory=list)
    scale: float=1.0
    offset: float=0.0
    partitions: int=DEFAULT_PARTITIONS
    group_by: str|None=None
    value_column: str|None=None
    aggregate: str="sum"
    select: list[str]=Field(default_factory=list)
    filters: list[FilterSpec]=Field(default_factory=list)

def _installed_pyspark_version():
    try: return importlib.metadata.version("pyspark")
    except importlib.metadata.PackageNotFoundError: return None

def _master():
    value=os.getenv("SC_SPARK_MASTER","local[2]")
    m=re.fullmatch(r"local\[(\*|\d+)\]",value)
    if not m: raise RuntimeError("SC_SPARK_MASTER must be a local[...] target in provider v1.0.0")
    if m.group(1)!="*" and int(m.group(1))>4: raise RuntimeError("SC_SPARK_MASTER exceeds v1.0.0 local thread limit")
    return value

def _validate_partitions(n):
    if n<1 or n>MAX_PARTITIONS: raise HTTPException(status_code=400,detail=f"partitions must be 1..{MAX_PARTITIONS}")
    return n

def _validate_values(values):
    if not values: raise HTTPException(status_code=400,detail="values must not be empty")
    if len(values)>MAX_NUMERIC_VALUES: raise HTTPException(status_code=400,detail=f"too many numeric values; max={MAX_NUMERIC_VALUES}")
    out=[]
    for v in values:
        f=float(v)
        if not math.isfinite(f): raise HTTPException(status_code=400,detail="values must be finite")
        out.append(f)
    return out

def _validate_rows(rows):
    if not rows: raise HTTPException(status_code=400,detail="rows must not be empty")
    if len(rows)>MAX_ROWS: raise HTTPException(status_code=400,detail=f"too many rows; max={MAX_ROWS}")
    columns=set()
    for row in rows:
        if not isinstance(row,dict): raise HTTPException(status_code=400,detail="each row must be an object")
        columns.update(row.keys())
        for k,v in row.items():
            if not isinstance(k,str) or not k or len(k)>128: raise HTTPException(status_code=400,detail="invalid column name")
            if isinstance(v,(dict,list,tuple,set)): raise HTTPException(status_code=400,detail="nested row values are not allowed in v1.0.0")
    if len(columns)>MAX_COLUMNS: raise HTTPException(status_code=400,detail=f"too many columns; max={MAX_COLUMNS}")
    return rows

def _spark_session():
    global _spark
    if _spark is None:
        try: from pyspark.sql import SparkSession
        except Exception as exc: raise HTTPException(status_code=503,detail=f"PySpark unavailable: {exc}") from exc
        local_dir=os.getenv("SC_SPARK_LOCAL_DIR","/var/lib/sc-spark-runtime/tmp")
        os.makedirs(local_dir,exist_ok=True)
        _spark=(SparkSession.builder.appName("SustainableCatalystSparkRuntime").master(_master())
            .config("spark.ui.enabled","false").config("spark.driver.bindAddress","127.0.0.1")
            .config("spark.driver.host","127.0.0.1").config("spark.sql.shuffle.partitions",str(MAX_PARTITIONS))
            .config("spark.default.parallelism",str(DEFAULT_PARTITIONS)).config("spark.local.dir",local_dir).getOrCreate())
        _spark.sparkContext.setLogLevel("ERROR")
    return _spark

def _adapter():
    return {"adapter_id":ADAPTER_ID,"adapter_contract":"sc.core.runtime-adapter.v1","provider_id":RUNTIME_ID,"provider_version":PROVIDER_VERSION,"native_runtime":"Apache Spark","native_runtime_version":SPARK_VERSION,"scala_binary_version":SCALA_BINARY_VERSION,"jvm_supported_versions":list(JVM_SUPPORTED),"runtime_kind":"distributed-analytics-execution-target","language":"spark-dataframe-rdd","status":"registered","execution_state":"active","transport":"HTTP","endpoint":"http://127.0.0.1:18106","capabilities":list(OPERATIONS),"lifecycle_methods":["health","version","capabilities","execute","inspect","collect_results","diagnose"],"boundaries":{"arbitrary_python_source":False,"arbitrary_scala_source":False,"arbitrary_java_source":False,"arbitrary_spark_sql":False,"caller_defined_udf":False,"caller_spark_conf":False,"runtime_dependency_install":False,"remote_cluster_selection":False,"external_data_source_access":False,"shell_execution":False,"public_network_listener":False}}

@app.get("/health")
def health():
    installed=_installed_pyspark_version()
    return {"ok":True,"runtime_id":RUNTIME_ID,"version":PROVIDER_VERSION,"spark_version_target":SPARK_VERSION,"pyspark_installed_version":installed,"pyspark_ready":installed==SPARK_VERSION,"scala_binary_version":SCALA_BINARY_VERSION,"master":_master(),"capabilities":len(OPERATIONS)}

@app.get("/v1/adapter")
def adapter(): return _adapter()

@app.get("/v1/capabilities")
def capabilities():
    return {"runtime_id":RUNTIME_ID,"provider_version":PROVIDER_VERSION,"operations":list(OPERATIONS),"limits":{"max_numeric_values":MAX_NUMERIC_VALUES,"max_rows":MAX_ROWS,"max_columns":MAX_COLUMNS,"max_partitions":MAX_PARTITIONS},"boundaries":_adapter()["boundaries"]}

@app.post("/v1/execute")
def execute(req: ExecuteRequest):
    if req.operation not in OPERATIONS: raise HTTPException(status_code=400,detail="unsupported operation")
    partitions=_validate_partitions(req.partitions); spark=_spark_session(); sc=spark.sparkContext
    if req.operation=="spark_runtime_info":
        result={"spark_version":spark.version,"master":sc.master,"application_name":sc.appName,"default_parallelism":sc.defaultParallelism,"scala_binary_version":SCALA_BINARY_VERSION}
    elif req.operation=="distributed_sum":
        values=_validate_values(req.values); rdd=sc.parallelize(values,partitions); result={"sum":float(rdd.sum()),"count":int(rdd.count()),"partitions":rdd.getNumPartitions()}
    elif req.operation=="distributed_map_affine":
        values=_validate_values(req.values); scale=float(req.scale); offset=float(req.offset)
        if not math.isfinite(scale) or not math.isfinite(offset): raise HTTPException(status_code=400,detail="scale and offset must be finite")
        rdd=sc.parallelize(values,partitions).map(lambda x:x*scale+offset); result={"values":[float(x) for x in rdd.collect()],"count":len(values),"partitions":rdd.getNumPartitions()}
    elif req.operation=="partition_summary":
        values=_validate_values(req.values); rdd=sc.parallelize(values,partitions)
        def summarize(it):
            xs=list(it)
            if not xs: return iter([])
            return iter([{"count":len(xs),"sum":float(sum(xs)),"min":float(min(xs)),"max":float(max(xs))}])
        result={"partitions":rdd.getNumPartitions(),"partition_summaries":rdd.mapPartitions(summarize).collect(),"count":len(values),"sum":float(sum(values))}
    elif req.operation=="dataframe_group_aggregate":
        rows=_validate_rows(req.rows)
        if not req.group_by or not req.value_column: raise HTTPException(status_code=400,detail="group_by and value_column are required")
        if req.aggregate not in ALLOWED_AGGREGATES: raise HTTPException(status_code=400,detail="unsupported aggregate")
        df=spark.createDataFrame(rows).repartition(partitions)
        if req.group_by not in df.columns or req.value_column not in df.columns: raise HTTPException(status_code=400,detail="group/value column not present")
        from pyspark.sql import functions as F
        agg_map={"sum":F.sum,"avg":F.avg,"count":F.count,"min":F.min,"max":F.max}
        out=df.groupBy(req.group_by).agg(agg_map[req.aggregate](req.value_column).alias("value")).orderBy(req.group_by)
        result={"rows":[r.asDict(recursive=False) for r in out.collect()],"group_by":req.group_by,"aggregate":req.aggregate}
    elif req.operation=="dataframe_filter_project":
        rows=_validate_rows(req.rows); df=spark.createDataFrame(rows).repartition(partitions)
        for spec in req.filters:
            if spec.op not in ALLOWED_FILTER_OPS: raise HTTPException(status_code=400,detail=f"unsupported filter op: {spec.op}")
            if spec.column not in df.columns: raise HTTPException(status_code=400,detail=f"filter column not present: {spec.column}")
            c=df[spec.column]; cond={"eq":c==spec.value,"neq":c!=spec.value,"gt":c>spec.value,"gte":c>=spec.value,"lt":c<spec.value,"lte":c<=spec.value}[spec.op]; df=df.filter(cond)
        selected=req.select or list(df.columns)
        if len(selected)>MAX_COLUMNS or any(c not in df.columns for c in selected): raise HTTPException(status_code=400,detail="invalid projection")
        out=df.select(*selected).limit(MAX_ROWS); result={"rows":[r.asDict(recursive=False) for r in out.collect()],"columns":selected}
    else: raise HTTPException(status_code=400,detail="operation not implemented")
    return {"ok":True,"run_id":f"spark-run:{uuid.uuid4()}","status":"completed","result":{"runtime_id":RUNTIME_ID,"runtime_version":PROVIDER_VERSION,"spark_version":SPARK_VERSION,"operation":req.operation,"result":result,"provenance":{"execution_mode":"provider-managed-local","master":_master(),"caller_spark_conf":False,"arbitrary_code_execution":False}}}
