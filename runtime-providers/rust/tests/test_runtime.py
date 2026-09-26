import pytest
from pydantic import ValidationError
from app.server import *


def test_identity():
    assert RUNTIME_ID == "sc-runtime-rust"
    assert ADAPTER_ID == "adapter:sc-runtime-rust"
    assert PROVIDER_VERSION == "1.0.0"
    assert RUSTC_VERSION == "1.75.0"
    assert CARGO_VERSION == "1.75.0"


def test_operations():
    assert OPERATIONS == ["prefix_sum","moving_average","connected_components","topological_sort","levenshtein_distance","fnv1a_64"]


def test_prefix_validation():
    assert validate_payload("prefix_sum", {"integers":[1,2,3]})["integers"] == [1,2,3]


def test_prefix_rejects_bool():
    with pytest.raises(ValueError): validate_payload("prefix_sum", {"integers":[True]})


def test_moving_average_validation():
    p=validate_payload("moving_average", {"values":[1,2,3],"window":2}); assert p["window"]==2


def test_moving_average_bad_window():
    with pytest.raises(ValueError): validate_payload("moving_average", {"values":[1,2],"window":3})


def test_components_validation():
    validate_payload("connected_components", {"adjacency_matrix":[[0,1],[1,0]]})


def test_components_rejects_asymmetric():
    with pytest.raises(ValueError): validate_payload("connected_components", {"adjacency_matrix":[[0,1],[0,0]]})


def test_topological_validation():
    validate_payload("topological_sort", {"vertex_count":3,"edge_list":[[0,1],[1,2]]})


def test_topological_rejects_out_of_range():
    with pytest.raises(ValueError): validate_payload("topological_sort", {"vertex_count":2,"edge_list":[[0,2]]})


def test_levenshtein_validation():
    validate_payload("levenshtein_distance", {"text_a":"kitten","text_b":"sitting"})


def test_levenshtein_rejects_non_ascii():
    with pytest.raises(ValueError): validate_payload("levenshtein_distance", {"text_a":"café","text_b":"cafe"})


def test_fnv_validation():
    validate_payload("fnv1a_64", {"text":"Sustainable Catalyst"})


@pytest.mark.parametrize("operation,payload,marker",[
    ("prefix_sum",{"integers":[1,2,3]},"SC_RESULT int_vector"),
    ("moving_average",{"values":[1,2,3],"window":2},"SC_RESULT vector"),
    ("connected_components",{"adjacency_matrix":[[0,1],[1,0]]},"SC_RESULT int_vector"),
    ("topological_sort",{"vertex_count":3,"edge_list":[[0,1],[1,2]]},"SC_RESULT int_vector"),
    ("levenshtein_distance",{"text_a":"kitten","text_b":"sitting"},"SC_RESULT int_scalar"),
    ("fnv1a_64",{"text":"abc"},"SC_RESULT hex64"),
])
def test_generated_source(operation,payload,marker):
    src=generated_source(operation,payload)
    assert src.startswith("#![forbid(unsafe_code)]")
    assert marker in src
    assert "unsafe {" not in src
    assert "Command::new" not in src


def test_parse_int_scalar():
    assert parse_output("SC_RESULT int_scalar 3\n")=={"kind":"int_scalar","value":3}


def test_parse_int_vector():
    assert parse_output("SC_RESULT int_vector 3\n1\n3\n6\n")["values"]==[1,3,6]


def test_parse_vector():
    assert parse_output("SC_RESULT vector 2\n1.5\n2.5\n")["values"]==[1.5,2.5]


def test_parse_hex():
    assert parse_output("SC_RESULT hex64 e71fa2190541574b\n")["value"]=="e71fa2190541574b"


def test_parse_bad_hex():
    with pytest.raises(ValueError): parse_output("SC_RESULT hex64 xyz\n")


def test_prepare_valid():
    req=PrepareRequest(operation="prefix_sum",payload={"integers":[1,2,3]}); assert req.operation=="prefix_sum"


def test_prepare_unknown():
    with pytest.raises(ValidationError): PrepareRequest(operation="shell",payload={})


def test_adapter_identity():
    d=adapter_descriptor(); assert d["adapter_id"]==ADAPTER_ID and d["provider_id"]==RUNTIME_ID and d["edition"]=="2021"


def test_adapter_boundaries():
    b=adapter_descriptor()["boundaries"]
    assert b["arbitrary_rust_source"] is False
    assert b["unsafe_rust_code"] is False
    assert b["shell_execution"] is False
    assert b["runtime_package_install"] is False
    assert b["caller_filesystem_paths"] is False


def test_fnv_known_value():
    # FNV-1a 64 of b"abc"
    h=0xcbf29ce484222325
    for b in b"abc": h=(h^b)*0x100000001b3 & 0xffffffffffffffff
    assert f"{h:016x}"=="e71fa2190541574b"
