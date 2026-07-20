"""Abu Experience Runtime contracts and deterministic theater primitives.

The package deliberately has no dependency on ``core.life_case``. Cognitive
authority enters through an immutable ``MingliExperienceEnvelope`` only.
"""

from experience.compiler import TopicCompileError, compile_topic, load_topic_package
from experience.canvas import (
    CanvasAction,
    CanvasContextPack,
    CanvasDiffSpec,
    CanvasCompileError,
    CanvasCompileRequest,
    MingliCanvasCompileInput,
    MingliCanvasSpec,
    TemporalSandboxState,
    apply_canvas_action,
    compile_canvas_context,
    compile_canvas_diff,
    compile_canvas_spec,
    create_temporal_sandbox,
    load_canvas_compile_input,
    project_canvas_spec_for_role,
    restore_temporal_sandbox,
)
from experience.contracts import (
    CompiledTopic,
    CueTemplate,
    MingliExperienceEnvelope,
    ParticipantRun,
    PerformancePackage,
    PerformanceCueInstance,
    TheaterEvent,
    TheaterSession,
    TopicExploration,
    TopicPackage,
)
from experience.cues import CueRenderError, freeze_performance_cue
from experience.performance import compile_performance_package

__all__ = [
    "CompiledTopic",
    "CanvasAction",
    "CanvasCompileError",
    "CanvasCompileRequest",
    "CanvasContextPack",
    "CanvasDiffSpec",
    "CueRenderError",
    "CueTemplate",
    "MingliExperienceEnvelope",
    "MingliCanvasCompileInput",
    "MingliCanvasSpec",
    "ParticipantRun",
    "PerformancePackage",
    "PerformanceCueInstance",
    "TheaterEvent",
    "TheaterSession",
    "TemporalSandboxState",
    "TopicCompileError",
    "TopicExploration",
    "TopicPackage",
    "compile_topic",
    "apply_canvas_action",
    "compile_canvas_context",
    "compile_canvas_diff",
    "compile_canvas_spec",
    "compile_performance_package",
    "freeze_performance_cue",
    "load_topic_package",
    "create_temporal_sandbox",
    "load_canvas_compile_input",
    "project_canvas_spec_for_role",
    "restore_temporal_sandbox",
]
