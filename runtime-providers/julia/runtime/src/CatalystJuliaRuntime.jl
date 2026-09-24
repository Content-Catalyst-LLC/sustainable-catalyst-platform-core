module CatalystJuliaRuntime

using Dates
using HTTP
using JSON3
using LinearAlgebra
using Pkg
using SHA
using Statistics
using TOML
using UUIDs

const SERVICE = "catalyst-julia-runtime"
const VERSION = "0.3.0"
const CONTRACT_VERSION = "sc.execution.v1"
const ENVIRONMENT_SCHEMA_VERSION = "sc.environment.v1"
const CORE_ADAPTER_CONTRACT_VERSION = "sc.core.runtime-adapter.v1"
const CORE_OBJECT_CONTRACT_VERSION = "sc.core.computational-runtime-object.v1"
const ADAPTER_ID = "adapter:catalyst-julia-runtime"
const MAX_BODY_BYTES = 1_048_576
const SAFE_ENV_KEYS = (
    "JULIA_DEPOT_PATH",
    "JULIA_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
)

json_response(status::Integer, value) = HTTP.Response(
    status,
    ["Content-Type" => "application/json; charset=utf-8"],
    JSON3.write(value),
)

function now_utc()
    Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ")
end

sha256_bytes(bytes) = bytes2hex(SHA.sha256(bytes))
sha256_json(value) = sha256_bytes(codeunits(JSON3.write(value)))

function sha256_file(path::AbstractString)
    isfile(path) || return nothing
    sha256_bytes(read(path))
end

function runtime_identity()
    Dict(
        "service" => SERVICE,
        "service_version" => VERSION,
        "runtime" => "julia",
        "runtime_version" => string(Base.VERSION),
        "contract_version" => CONTRACT_VERSION,
        "environment_schema_version" => ENVIRONMENT_SCHEMA_VERSION,
        "core_adapter_contract_version" => CORE_ADAPTER_CONTRACT_VERSION,
        "core_object_contract_version" => CORE_OBJECT_CONTRACT_VERSION,
        "adapter_id" => ADAPTER_ID,
    )
end

function capability_document()
    Dict(
        "identity" => runtime_identity(),
        "execution_mode" => "allowlisted-operations",
        "arbitrary_code_execution" => false,
        "shell_execution" => false,
        "package_installation" => false,
        "environment_inspection" => true,
        "environment_fingerprint" => true,
        "dependency_inventory" => true,
        "expected_environment_guard" => true,
        "core_adapter_contract" => CORE_ADAPTER_CONTRACT_VERSION,
        "core_object_contract" => CORE_OBJECT_CONTRACT_VERSION,
        "adapter_lifecycle" => [
            "health",
            "version",
            "capabilities",
            "prepare",
            "execute",
            "cancel",
            "inspect",
            "collect_results",
            "collect_artifacts",
            "diagnose",
        ],
        "operations" => [
            Dict("name"=>"identity", "deterministic"=>true),
            Dict("name"=>"sum", "deterministic"=>true),
            Dict("name"=>"mean", "deterministic"=>true),
            Dict("name"=>"matrix_multiply", "deterministic"=>true),
        ],
        "limits" => Dict("max_request_bytes" => MAX_BODY_BYTES),
    )
end

function active_project_paths()
    project_path = Base.active_project()
    project_path === nothing && return (nothing, nothing)
    manifest_path = joinpath(dirname(project_path), "Manifest.toml")
    (project_path, manifest_path)
end

function safe_environment_variables()
    result = Dict{String,Any}()
    for key in SAFE_ENV_KEYS
        if haskey(ENV, key)
            result[key] = ENV[key]
        end
    end
    result
end

function package_inventory()
    items = Vector{Dict{String,Any}}()
    for (uuid, info) in Pkg.dependencies()
        push!(items, Dict(
            "name" => info.name,
            "uuid" => string(uuid),
            "version" => info.version === nothing ? nothing : string(info.version),
            "tree_hash" => info.tree_hash === nothing ? nothing : string(info.tree_hash),
            "direct" => info.is_direct_dep,
        ))
    end
    sort!(items, by = item -> (string(get(item, "name", "")), item["uuid"]))
    items
end

function canonical_environment_fingerprint(project_sha, manifest_sha, packages)
    parts = String[
        "schema=$(ENVIRONMENT_SCHEMA_VERSION)",
        "runtime=julia",
        "runtime_version=$(Base.VERSION)",
        "arch=$(Sys.ARCH)",
        "word_size=$(Sys.WORD_SIZE)",
        "project_sha256=$(project_sha === nothing ? "missing" : project_sha)",
        "manifest_sha256=$(manifest_sha === nothing ? "missing" : manifest_sha)",
    ]
    for package in packages
        push!(parts, join((
            "pkg",
            package["uuid"],
            string(package["name"]),
            package["version"] === nothing ? "" : string(package["version"]),
            package["tree_hash"] === nothing ? "" : string(package["tree_hash"]),
            package["direct"] ? "direct" : "transitive",
        ), "|"))
    end
    sha256_bytes(codeunits(join(parts, "\n")))
end

function host_fingerprint(environment_sha)
    parts = String[
        "environment_sha256=$environment_sha",
        "kernel=$(Sys.KERNEL)",
        "arch=$(Sys.ARCH)",
        "word_size=$(Sys.WORD_SIZE)",
        "cpu_threads=$(Sys.CPU_THREADS)",
    ]
    sha256_bytes(codeunits(join(parts, "\n")))
end

function environment_document()
    project_path, manifest_path = active_project_paths()
    project_sha = project_path === nothing ? nothing : sha256_file(project_path)
    manifest_sha = manifest_path === nothing ? nothing : sha256_file(manifest_path)
    packages = package_inventory()
    environment_sha = canonical_environment_fingerprint(project_sha, manifest_sha, packages)

    Dict(
        "schema_version" => ENVIRONMENT_SCHEMA_VERSION,
        "captured_at" => now_utc(),
        "identity" => runtime_identity(),
        "project" => Dict(
            "path" => project_path,
            "sha256" => project_sha,
        ),
        "manifest" => Dict(
            "path" => manifest_path,
            "present" => manifest_path !== nothing && isfile(manifest_path),
            "sha256" => manifest_sha,
        ),
        "dependencies" => packages,
        "platform" => Dict(
            "kernel" => string(Sys.KERNEL),
            "architecture" => string(Sys.ARCH),
            "word_size" => Sys.WORD_SIZE,
            "cpu_threads" => Sys.CPU_THREADS,
        ),
        "julia" => Dict(
            "version" => string(Base.VERSION),
            "threads" => Threads.nthreads(),
            "depot_paths" => copy(Base.DEPOT_PATH),
        ),
        "environment_variables" => safe_environment_variables(),
        "fingerprints" => Dict(
            "environment_sha256" => environment_sha,
            "host_sha256" => host_fingerprint(environment_sha),
        ),
        "reproducibility" => Dict(
            "lock_state" => manifest_sha === nothing ? "unlocked" : "locked",
            "manifest_present" => manifest_sha !== nothing,
            "package_installation_at_runtime" => false,
            "expected_environment_guard" => true,
        ),
    )
end

function environment_fingerprint()
    environment_document()["fingerprints"]["environment_sha256"]
end

function require_dict(value, name)
    value isa AbstractDict || throw(ArgumentError("$name must be an object"))
    value
end

function normalize_job(payload)
    require_dict(payload, "job")
    operation = String(get(payload, "operation", ""))
    isempty(operation) && throw(ArgumentError("operation is required"))
    operation in ("identity", "sum", "mean", "matrix_multiply") ||
        throw(ArgumentError("operation is not registered"))

    job_id = String(get(payload, "job_id", string(uuid4())))
    inputs = get(payload, "inputs", Dict{String,Any}())
    parameters = get(payload, "parameters", Dict{String,Any}())
    provenance = get(payload, "provenance", Dict{String,Any}())
    expected_environment = get(payload, "expected_environment_fingerprint_sha256", nothing)

    require_dict(inputs, "inputs")
    require_dict(parameters, "parameters")
    require_dict(provenance, "provenance")
    if expected_environment !== nothing
        expected_environment isa AbstractString ||
            throw(ArgumentError("expected_environment_fingerprint_sha256 must be a string"))
        isempty(expected_environment) &&
            throw(ArgumentError("expected_environment_fingerprint_sha256 must not be empty"))
    end

    Dict(
        "job_id" => job_id,
        "operation" => operation,
        "inputs" => inputs,
        "parameters" => parameters,
        "provenance" => provenance,
        "expected_environment_fingerprint_sha256" => expected_environment,
    )
end

function enforce_environment_expectation(job, actual_fingerprint)
    expected = get(job, "expected_environment_fingerprint_sha256", nothing)
    if expected !== nothing && expected != actual_fingerprint
        throw(ArgumentError(
            "environment fingerprint mismatch: expected $expected but runtime is $actual_fingerprint"
        ))
    end
    nothing
end

number_vector(v, name) = begin
    v isa AbstractVector || throw(ArgumentError("$name must be an array"))
    all(x -> x isa Number, v) || throw(ArgumentError("$name must contain only numbers"))
    Float64.(v)
end

function number_matrix(v, name)
    v isa AbstractVector || throw(ArgumentError("$name must be an array of rows"))
    isempty(v) && throw(ArgumentError("$name must not be empty"))
    all(row -> row isa AbstractVector, v) || throw(ArgumentError("$name must contain row arrays"))
    widths = unique(length.(v))
    length(widths) == 1 || throw(ArgumentError("$name must be rectangular"))
    all(row -> all(x -> x isa Number, row), v) || throw(ArgumentError("$name must contain only numbers"))
    reduce(vcat, [permutedims(Float64.(row)) for row in v])
end

function execute_operation(job)
    op = job["operation"]
    inputs = job["inputs"]

    if op == "identity"
        return get(inputs, "value", nothing)
    elseif op == "sum"
        values = number_vector(get(inputs, "values", Any[]), "inputs.values")
        return sum(values)
    elseif op == "mean"
        values = number_vector(get(inputs, "values", Any[]), "inputs.values")
        isempty(values) && throw(ArgumentError("inputs.values must not be empty"))
        return mean(values)
    elseif op == "matrix_multiply"
        a = number_matrix(get(inputs, "a", Any[]), "inputs.a")
        b = number_matrix(get(inputs, "b", Any[]), "inputs.b")
        size(a, 2) == size(b, 1) || throw(ArgumentError("matrix dimensions are incompatible"))
        return [collect(row) for row in eachrow(a * b)]
    end

    error("unreachable operation")
end


const EXECUTION_RECORDS = Dict{String,Dict{String,Any}}()
const RESULT_RECORDS = Dict{String,Dict{String,Any}}()

function core_adapter_descriptor()
    Dict(
        "adapter_id" => ADAPTER_ID,
        "adapter_contract" => CORE_ADAPTER_CONTRACT_VERSION,
        "runtime" => Dict(
            "runtime_id" => SERVICE,
            "runtime_kind" => "language",
            "language" => "julia",
            "implementation" => "Julia",
            "runtime_version" => string(Base.VERSION),
            "provider_version" => VERSION,
            "service_name" => SERVICE,
            "contract_versions" => [
                CORE_OBJECT_CONTRACT_VERSION,
                CORE_ADAPTER_CONTRACT_VERSION,
                CONTRACT_VERSION,
                ENVIRONMENT_SCHEMA_VERSION,
            ],
            "status" => "active",
            "execution_host" => "contabo-vps",
        ),
        "provider_contracts" => [
            CONTRACT_VERSION,
            ENVIRONMENT_SCHEMA_VERSION,
        ],
        "transport" => "http",
        "invocation_mode" => "governed-service",
        "service_ref" => SERVICE,
        "methods" => [
            Dict("name"=>"health", "required"=>true, "idempotent"=>true),
            Dict("name"=>"version", "required"=>true, "idempotent"=>true),
            Dict("name"=>"capabilities", "required"=>true, "idempotent"=>true),
            Dict("name"=>"prepare", "required"=>true, "idempotent"=>true),
            Dict("name"=>"execute", "required"=>true, "idempotent"=>false),
            Dict("name"=>"cancel", "required"=>true, "idempotent"=>true),
            Dict("name"=>"inspect", "required"=>true, "idempotent"=>true),
            Dict("name"=>"collect_results", "required"=>true, "idempotent"=>true),
            Dict("name"=>"collect_artifacts", "required"=>true, "idempotent"=>true),
            Dict("name"=>"diagnose", "required"=>true, "idempotent"=>true),
        ],
        "status" => "registered",
        "metadata" => Dict(
            "reference_adapter" => true,
            "core_executes_runtime_directly" => false,
            "execution_mode" => "synchronous-governed-operation",
            "arbitrary_code_execution" => false,
            "shell_execution" => false,
            "package_installation" => false,
        ),
    )
end

function normalize_core_request(payload)
    require_dict(payload, "execution_request")
    request_id = String(get(payload, "request_id", get(payload, "job_id", string(uuid4()))))
    runtime_id = String(get(payload, "runtime_id", SERVICE))
    runtime_id == SERVICE || throw(ArgumentError("runtime_id must be catalyst-julia-runtime"))
    operation = get(payload, "operation", nothing)
    operation === nothing && throw(ArgumentError("operation is required"))
    job = Dict(
        "job_id" => request_id,
        "operation" => String(operation),
        "inputs" => get(payload, "inputs", Dict{String,Any}()),
        "parameters" => get(payload, "parameters", Dict{String,Any}()),
        "provenance" => get(payload, "provenance", Dict{String,Any}()),
        "expected_environment_fingerprint_sha256" =>
            get(payload, "expected_environment_fingerprint_sha256", nothing),
    )
    normalized_job = normalize_job(job)
    Dict(
        "request_id" => request_id,
        "runtime_id" => runtime_id,
        "environment_id" => get(payload, "environment_id", nothing),
        "operation" => normalized_job["operation"],
        "inputs" => normalized_job["inputs"],
        "parameters" => normalized_job["parameters"],
        "expected_environment_fingerprint_sha256" =>
            normalized_job["expected_environment_fingerprint_sha256"],
        "provenance" => normalized_job["provenance"],
    )
end

function adapter_prepare(payload)
    request = normalize_core_request(payload)
    environment_sha = environment_fingerprint()
    enforce_environment_expectation(Dict(
        "expected_environment_fingerprint_sha256" =>
            request["expected_environment_fingerprint_sha256"]
    ), environment_sha)

    run_id = "run:" * string(uuid4())
    record = Dict(
        "run_id" => run_id,
        "request_id" => request["request_id"],
        "runtime_id" => SERVICE,
        "state" => "prepared",
        "operation" => request["operation"],
        "prepared_at" => now_utc(),
        "environment_fingerprint_sha256" => environment_sha,
        "request" => request,
        "diagnostics" => Any[],
    )
    EXECUTION_RECORDS[run_id] = record
    Dict(
        "ok" => true,
        "adapter_contract" => CORE_ADAPTER_CONTRACT_VERSION,
        "run" => record,
    )
end

function adapter_execute(payload)
    request = normalize_core_request(payload)
    started = time_ns()
    submitted_at = now_utc()
    environment = environment_document()
    environment_sha = environment["fingerprints"]["environment_sha256"]
    enforce_environment_expectation(Dict(
        "expected_environment_fingerprint_sha256" =>
            request["expected_environment_fingerprint_sha256"]
    ), environment_sha)

    run_id = String(get(payload, "run_id", "run:" * string(uuid4())))
    execution_id = string(uuid4())
    job = Dict(
        "job_id" => request["request_id"],
        "operation" => request["operation"],
        "inputs" => request["inputs"],
        "parameters" => request["parameters"],
        "provenance" => request["provenance"],
        "expected_environment_fingerprint_sha256" =>
            request["expected_environment_fingerprint_sha256"],
    )
    result_value = execute_operation(job)
    elapsed_ms = (time_ns() - started) / 1_000_000
    completed_at = now_utc()
    input_hash = sha256_json(request["inputs"])

    run = Dict(
        "run_id" => run_id,
        "request_id" => request["request_id"],
        "runtime_id" => SERVICE,
        "state" => "completed",
        "external_execution_ref" => execution_id,
        "started_at" => submitted_at,
        "finished_at" => completed_at,
        "elapsed_ms" => elapsed_ms,
        "environment_fingerprint_sha256" => environment_sha,
        "diagnostics" => Any[],
    )
    result_id = "result:" * execution_id
    result = Dict(
        "result_id" => result_id,
        "run_id" => run_id,
        "request_id" => request["request_id"],
        "runtime_id" => SERVICE,
        "state" => "completed",
        "environment_fingerprint_sha256" => environment_sha,
        "scalar_result" => result_value isa Number || result_value isa AbstractString ||
            result_value isa Bool || result_value === nothing ? result_value : nothing,
        "structured_result" => result_value isa AbstractDict || result_value isa AbstractVector ?
            result_value : nothing,
        "artifact_refs" => String[],
        "diagnostics" => Any[],
        "provenance" => request["provenance"],
        "completed_at" => completed_at,
        "metadata" => Dict(
            "operation" => request["operation"],
            "input_hash_sha256" => input_hash,
            "environment_lock_state" => environment["reproducibility"]["lock_state"],
        ),
    )
    EXECUTION_RECORDS[run_id] = run
    RESULT_RECORDS[run_id] = result

    Dict(
        "ok" => true,
        "adapter_contract" => CORE_ADAPTER_CONTRACT_VERSION,
        "run" => run,
        "result" => result,
    )
end

function adapter_cancel(payload)
    require_dict(payload, "cancel_request")
    run_id = String(get(payload, "run_id", ""))
    isempty(run_id) && throw(ArgumentError("run_id is required"))
    record = get(EXECUTION_RECORDS, run_id, nothing)
    if record === nothing
        return Dict(
            "ok" => true,
            "adapter_contract" => CORE_ADAPTER_CONTRACT_VERSION,
            "run_id" => run_id,
            "state" => "not_found",
            "cancelled" => false,
        )
    end
    state = String(get(record, "state", "unknown"))
    if state in ("completed", "failed", "cancelled")
        return Dict(
            "ok" => true,
            "adapter_contract" => CORE_ADAPTER_CONTRACT_VERSION,
            "run_id" => run_id,
            "state" => state,
            "cancelled" => false,
            "reason" => "terminal_state",
        )
    end
    record["state"] = "cancelled"
    record["finished_at"] = now_utc()
    EXECUTION_RECORDS[run_id] = record
    Dict(
        "ok" => true,
        "adapter_contract" => CORE_ADAPTER_CONTRACT_VERSION,
        "run_id" => run_id,
        "state" => "cancelled",
        "cancelled" => true,
    )
end

function adapter_inspect(run_id::AbstractString)
    record = get(EXECUTION_RECORDS, String(run_id), nothing)
    record === nothing && return Dict(
        "ok" => false,
        "adapter_contract" => CORE_ADAPTER_CONTRACT_VERSION,
        "run_id" => String(run_id),
        "state" => "not_found",
    )
    Dict(
        "ok" => true,
        "adapter_contract" => CORE_ADAPTER_CONTRACT_VERSION,
        "run" => record,
    )
end

function adapter_collect_results(run_id::AbstractString)
    result = get(RESULT_RECORDS, String(run_id), nothing)
    result === nothing && return Dict(
        "ok" => true,
        "adapter_contract" => CORE_ADAPTER_CONTRACT_VERSION,
        "run_id" => String(run_id),
        "results" => Any[],
    )
    Dict(
        "ok" => true,
        "adapter_contract" => CORE_ADAPTER_CONTRACT_VERSION,
        "run_id" => String(run_id),
        "results" => [result],
    )
end

function adapter_collect_artifacts(run_id::AbstractString)
    Dict(
        "ok" => true,
        "adapter_contract" => CORE_ADAPTER_CONTRACT_VERSION,
        "run_id" => String(run_id),
        "artifacts" => Any[],
        "artifact_transport" => "none-for-built-in-scalar-array-matrix-operations",
    )
end

function adapter_diagnose(run_id::Union{Nothing,AbstractString}=nothing)
    diagnostics = Any[]
    if run_id !== nothing
        record = get(EXECUTION_RECORDS, String(run_id), nothing)
        if record === nothing
            push!(diagnostics, Dict(
                "level" => "info",
                "code" => "run_not_found",
                "message" => "No in-memory execution record exists for the requested run.",
            ))
        else
            append!(diagnostics, get(record, "diagnostics", Any[]))
        end
    end
    Dict(
        "ok" => true,
        "adapter_contract" => CORE_ADAPTER_CONTRACT_VERSION,
        "run_id" => run_id,
        "runtime" => runtime_identity(),
        "environment_fingerprint_sha256" => environment_fingerprint(),
        "diagnostics" => diagnostics,
        "persistence" => "in-memory-execution-registry",
    )
end

function query_param(req, key::AbstractString)
    uri = HTTP.URI(req.target)
    query = HTTP.URIs.queryparams(uri)
    get(query, String(key), nothing)
end

function required_run_id(req)
    value = query_param(req, "run_id")
    value === nothing && throw(ArgumentError("run_id query parameter is required"))
    String(value)
end

function adapter_prepare_handler(req)
    json_response(200, adapter_prepare(parse_body(req)))
end

function adapter_execute_handler(req)
    json_response(200, adapter_execute(parse_body(req)))
end

function adapter_cancel_handler(req)
    json_response(200, adapter_cancel(parse_body(req)))
end

function adapter_inspect_handler(req)
    json_response(200, adapter_inspect(required_run_id(req)))
end

function adapter_results_handler(req)
    json_response(200, adapter_collect_results(required_run_id(req)))
end

function adapter_artifacts_handler(req)
    json_response(200, adapter_collect_artifacts(required_run_id(req)))
end

function adapter_diagnose_handler(req)
    run_id = query_param(req, "run_id")
    json_response(200, adapter_diagnose(run_id))
end


function parse_body(req)
    length(req.body) <= MAX_BODY_BYTES || throw(ArgumentError("request body exceeds size limit"))
    isempty(req.body) && return Dict{String,Any}()
    JSON3.read(String(req.body), Dict{String,Any})
end

function validate_handler(req)
    job = normalize_job(parse_body(req))
    actual_fingerprint = environment_fingerprint()
    enforce_environment_expectation(job, actual_fingerprint)
    json_response(200, Dict(
        "valid" => true,
        "job" => job,
        "identity" => runtime_identity(),
        "environment_fingerprint_sha256" => actual_fingerprint,
    ))
end

function run_handler(req)
    started = time_ns()
    submitted_at = now_utc()
    job = normalize_job(parse_body(req))
    environment = environment_document()
    environment_sha = environment["fingerprints"]["environment_sha256"]
    enforce_environment_expectation(job, environment_sha)
    input_hash = sha256_json(job["inputs"])
    result = execute_operation(job)
    elapsed_ms = (time_ns() - started) / 1_000_000

    envelope = Dict(
        "execution_id" => string(uuid4()),
        "job_id" => job["job_id"],
        "status" => "succeeded",
        "submitted_at" => submitted_at,
        "completed_at" => now_utc(),
        "elapsed_ms" => elapsed_ms,
        "operation" => job["operation"],
        "runtime" => runtime_identity(),
        "input_hash_sha256" => input_hash,
        "environment_fingerprint_sha256" => environment_sha,
        "environment_lock_state" => environment["reproducibility"]["lock_state"],
        "provenance" => job["provenance"],
        "result" => result,
    )
    json_response(200, envelope)
end

function request_handler(req)
    try
        path = HTTP.URI(req.target).path
        method = String(req.method)

        if method == "GET" && path == "/health"
            return json_response(200, Dict(
                "status" => "ok",
                "time" => now_utc(),
                "identity" => runtime_identity(),
                "environment_fingerprint_sha256" => environment_fingerprint(),
            ))
        elseif method == "GET" && path == "/version"
            return json_response(200, runtime_identity())
        elseif method == "GET" && path == "/capabilities"
            return json_response(200, capability_document())
        elseif method == "GET" && path in ("/environment", "/v1/environment")
            return json_response(200, environment_document())
        elseif method == "GET" && path == "/v1/environment/fingerprint"
            return json_response(200, Dict(
                "schema_version" => ENVIRONMENT_SCHEMA_VERSION,
                "environment_fingerprint_sha256" => environment_fingerprint(),
            ))
        elseif method == "POST" && path == "/v1/jobs/validate"
            return validate_handler(req)
        elseif method == "POST" && path == "/v1/jobs/run"
            return run_handler(req)
        elseif method == "GET" && path == "/v1/core-adapter"
            return json_response(200, core_adapter_descriptor())
        elseif method == "POST" && path == "/v1/core-adapter/prepare"
            return adapter_prepare_handler(req)
        elseif method == "POST" && path == "/v1/core-adapter/execute"
            return adapter_execute_handler(req)
        elseif method == "POST" && path == "/v1/core-adapter/cancel"
            return adapter_cancel_handler(req)
        elseif method == "GET" && path == "/v1/core-adapter/inspect"
            return adapter_inspect_handler(req)
        elseif method == "GET" && path == "/v1/core-adapter/results"
            return adapter_results_handler(req)
        elseif method == "GET" && path == "/v1/core-adapter/artifacts"
            return adapter_artifacts_handler(req)
        elseif method == "GET" && path == "/v1/core-adapter/diagnose"
            return adapter_diagnose_handler(req)
        end

        json_response(404, Dict("error"=>"not_found", "path"=>path))
    catch err
        status = err isa ArgumentError ? 400 : 500
        json_response(status, Dict(
            "error" => status == 400 ? "invalid_request" : "internal_error",
            "message" => sprint(showerror, err),
        ))
    end
end

function serve(; host="127.0.0.1", port=18093)
    @info "Starting Catalyst Julia Runtime" host=host port=port version=VERSION julia=Base.VERSION
    HTTP.serve(request_handler, host, port; verbose=false)
end

export serve, request_handler, runtime_identity, capability_document,
       environment_document, environment_fingerprint, normalize_job,
       enforce_environment_expectation, execute_operation, core_adapter_descriptor,
       normalize_core_request, adapter_prepare, adapter_execute, adapter_cancel,
       adapter_inspect, adapter_collect_results, adapter_collect_artifacts,
       adapter_diagnose

end
