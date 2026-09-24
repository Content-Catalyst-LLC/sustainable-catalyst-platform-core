using Test
using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))
using CatalystJuliaRuntime

@testset "runtime identity" begin
    identity = CatalystJuliaRuntime.runtime_identity()
    @test identity["service"] == "catalyst-julia-runtime"
    @test identity["service_version"] == "0.3.0"
    @test identity["runtime"] == "julia"
    @test identity["environment_schema_version"] == "sc.environment.v1"
    @test identity["core_adapter_contract_version"] == "sc.core.runtime-adapter.v1"
    @test identity["core_object_contract_version"] == "sc.core.computational-runtime-object.v1"
end

@testset "environment snapshot" begin
    env = CatalystJuliaRuntime.environment_document()
    @test env["schema_version"] == "sc.environment.v1"
    @test env["identity"]["service_version"] == "0.3.0"
    @test length(env["dependencies"]) > 0
    @test length(env["fingerprints"]["environment_sha256"]) == 64
    @test env["reproducibility"]["expected_environment_guard"] == true
end

@testset "environment fingerprint stability" begin
    a = CatalystJuliaRuntime.environment_fingerprint()
    b = CatalystJuliaRuntime.environment_fingerprint()
    @test a == b
    @test length(a) == 64
end

@testset "job normalization" begin
    job = CatalystJuliaRuntime.normalize_job(Dict(
        "job_id"=>"t1", "operation"=>"sum", "inputs"=>Dict("values"=>[1,2,3])
    ))
    @test job["job_id"] == "t1"
    @test job["operation"] == "sum"
end

@testset "environment expectation guard" begin
    fingerprint = CatalystJuliaRuntime.environment_fingerprint()
    job = CatalystJuliaRuntime.normalize_job(Dict(
        "operation"=>"identity",
        "inputs"=>Dict("value"=>1),
        "expected_environment_fingerprint_sha256"=>fingerprint,
    ))
    @test CatalystJuliaRuntime.enforce_environment_expectation(job, fingerprint) === nothing
    bad = copy(job)
    bad["expected_environment_fingerprint_sha256"] = repeat("0", 64)
    @test_throws ArgumentError CatalystJuliaRuntime.enforce_environment_expectation(bad, fingerprint)
end

@testset "allowlisted execution" begin
    @test CatalystJuliaRuntime.execute_operation(Dict("operation"=>"identity", "inputs"=>Dict("value"=>7))) == 7
    @test CatalystJuliaRuntime.execute_operation(Dict("operation"=>"sum", "inputs"=>Dict("values"=>[1,2,3]))) == 6.0
    @test CatalystJuliaRuntime.execute_operation(Dict("operation"=>"mean", "inputs"=>Dict("values"=>[1,2,3]))) == 2.0
    matrix = CatalystJuliaRuntime.execute_operation(Dict(
        "operation"=>"matrix_multiply",
        "inputs"=>Dict("a"=>[[1,2],[3,4]], "b"=>[[5,6],[7,8]])
    ))
    @test matrix == [[19.0,22.0],[43.0,50.0]]
end

@testset "core adapter descriptor" begin
    descriptor = CatalystJuliaRuntime.core_adapter_descriptor()
    @test descriptor["adapter_id"] == "adapter:catalyst-julia-runtime"
    @test descriptor["adapter_contract"] == "sc.core.runtime-adapter.v1"
    @test descriptor["status"] == "registered"
    @test descriptor["runtime"]["provider_version"] == "0.3.0"
    @test length(descriptor["methods"]) == 10
    @test Set(m["name"] for m in descriptor["methods"]) == Set([
        "health", "version", "capabilities", "prepare", "execute", "cancel",
        "inspect", "collect_results", "collect_artifacts", "diagnose"
    ])
end

@testset "core adapter prepare execute inspect collect" begin
    env = CatalystJuliaRuntime.environment_fingerprint()
    prepared = CatalystJuliaRuntime.adapter_prepare(Dict(
        "request_id"=>"request:test-sum",
        "runtime_id"=>"catalyst-julia-runtime",
        "operation"=>"sum",
        "inputs"=>Dict("values"=>[1,2,3,4]),
        "expected_environment_fingerprint_sha256"=>env,
        "provenance"=>Dict("purpose"=>"julia-v030-test"),
    ))
    @test prepared["ok"] == true
    @test prepared["run"]["state"] == "prepared"

    executed = CatalystJuliaRuntime.adapter_execute(Dict(
        "request_id"=>"request:test-sum",
        "runtime_id"=>"catalyst-julia-runtime",
        "run_id"=>prepared["run"]["run_id"],
        "operation"=>"sum",
        "inputs"=>Dict("values"=>[1,2,3,4]),
        "expected_environment_fingerprint_sha256"=>env,
        "provenance"=>Dict("purpose"=>"julia-v030-test"),
    ))
    run_id = executed["run"]["run_id"]
    @test executed["run"]["state"] == "completed"
    @test executed["result"]["state"] == "completed"
    @test executed["result"]["scalar_result"] == 10.0
    @test CatalystJuliaRuntime.adapter_inspect(run_id)["run"]["state"] == "completed"
    @test length(CatalystJuliaRuntime.adapter_collect_results(run_id)["results"]) == 1
    @test CatalystJuliaRuntime.adapter_collect_artifacts(run_id)["artifacts"] == Any[]
    @test CatalystJuliaRuntime.adapter_diagnose(run_id)["ok"] == true
end

@testset "core adapter cancellation semantics" begin
    prepared = CatalystJuliaRuntime.adapter_prepare(Dict(
        "request_id"=>"request:test-cancel",
        "runtime_id"=>"catalyst-julia-runtime",
        "operation"=>"identity",
        "inputs"=>Dict("value"=>1),
    ))
    run_id = prepared["run"]["run_id"]
    cancelled = CatalystJuliaRuntime.adapter_cancel(Dict("run_id"=>run_id))
    @test cancelled["cancelled"] == true
    @test cancelled["state"] == "cancelled"
    @test CatalystJuliaRuntime.adapter_inspect(run_id)["run"]["state"] == "cancelled"
end
