#!/usr/bin/env julia
using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))
using CatalystJuliaRuntime

host = get(ENV, "SC_JULIA_HOST", "127.0.0.1")
port = parse(Int, get(ENV, "SC_JULIA_PORT", "18093"))
CatalystJuliaRuntime.serve(host=host, port=port)
