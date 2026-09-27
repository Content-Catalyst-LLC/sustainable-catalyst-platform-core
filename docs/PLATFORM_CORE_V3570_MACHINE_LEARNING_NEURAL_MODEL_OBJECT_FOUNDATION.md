# Platform Core v3.57.0 — Machine Learning & Neural Model Object Foundation

v3.57.0 adds a governed, framework-neutral machine-learning object layer above the existing v3.27 AI Model & Model-Version Object Model and the later computational runtime fabric.

## New objects

`MLFeatureSpec`, `MLFeatureSchema`, `NeuralLayerSpec`, `NeuralArchitectureSpec`, `MLObjectiveSpec`, `MLRuntimeBinding`, `MLModelSpecification`, `MLDataSplitSpec`, `MLTrainingPlan`, `MLInferencePlan`, and `MLModelBundle`.

## Deep-learning readiness

Declarative architecture types include MLP, CNN, RNN/LSTM/GRU, Transformer, graph neural networks, autoencoders/VAEs, diffusion, hybrid, and extensible other architectures. Layer graphs and tensor shapes are descriptive and fingerprintable; they are not executable source code.

## Integration

The release reuses v3.27 AI model/model-version identity references, dataset-version lineage, computational job contracts, runtime adapter registry, execution-environment provenance, and Workspace/Lab execution boundaries.

**Architecture rule:** Core defines. Workspace computes. Lab experiments. Products consume.

## Hard boundaries

Core does not train models, run inference, install ML packages, accept arbitrary executable model code, autonomously select/rank models, certify model quality, or promote predictions to truth.
