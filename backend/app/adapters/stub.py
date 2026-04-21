from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StubAgentAdapter:
    def run_task(self, input_text: str, config: dict[str, object]) -> dict[str, object]:
        dataset_item_id = str(config.get("dataset_item_id", "unknown"))
        expected_output = config.get("expected_output")
        failure_map = config.get("failure_map", {})
        answer_incorrect_map = config.get("answer_incorrect_map", {})
        tool_failure_map = config.get("tool_failure_map", {})
        format_failure_map = config.get("format_failure_map", {})
        tool_call_map = config.get("tool_call_map", {})
        failure_mode = str(config.get("failure_mode", "none"))
        force_expected_output = bool(config.get("force_expected_output", True))

        should_execution_fail = isinstance(failure_map, dict) and bool(
            failure_map.get(dataset_item_id)
        )
        should_tool_fail = isinstance(tool_failure_map, dict) and bool(
            tool_failure_map.get(dataset_item_id)
        )
        should_answer_incorrect = isinstance(answer_incorrect_map, dict) and bool(
            answer_incorrect_map.get(dataset_item_id)
        )
        should_format_fail = isinstance(format_failure_map, dict) and bool(
            format_failure_map.get(dataset_item_id)
        )
        should_include_tool_call = (
            should_tool_fail
            or isinstance(tool_call_map, dict)
            and bool(tool_call_map.get(dataset_item_id))
        )

        if failure_mode == "all":
            should_execution_fail = True

        if should_tool_fail:
            return {
                "final_output": None,
                "latency_ms": 120,
                "token_usage": {"prompt": 100, "completion": 12},
                "cost": 0.0005,
                "termination_reason": "tool_error",
                "error": f"Deterministic tool failure for {dataset_item_id}.",
                "trace_events": [
                    {"step_index": 0, "event_type": "agent_start", "input": input_text},
                    {
                        "step_index": 1,
                        "event_type": "tool_call",
                        "tool_name": "document_lookup",
                        "input": {"query": input_text[:80]},
                        "status": "error",
                        "latency_ms": 41,
                        "error": f"Deterministic tool failure for {dataset_item_id}.",
                    },
                    {
                        "step_index": 2,
                        "event_type": "agent_error",
                        "error": f"Deterministic tool failure for {dataset_item_id}.",
                    },
                ],
            }

        if should_execution_fail:
            return {
                "final_output": None,
                "latency_ms": 120,
                "token_usage": {"prompt": 100, "completion": 5},
                "cost": 0.0005,
                "termination_reason": "failed",
                "error": f"Deterministic stub failure for {dataset_item_id}.",
                "trace_events": [
                    {"step_index": 0, "event_type": "agent_start", "input": input_text},
                    {
                        "step_index": 1,
                        "event_type": "agent_error",
                        "error": f"Deterministic stub failure for {dataset_item_id}.",
                    },
                ],
            }

        if should_format_fail:
            return {
                "final_output": "response=unstructured",
                "latency_ms": 120,
                "token_usage": {"prompt": 100, "completion": 25},
                "cost": 0.0008,
                "termination_reason": "format_error",
                "error": None,
                "trace_events": [
                    {"step_index": 0, "event_type": "agent_start", "input": input_text},
                    {
                        "step_index": 1,
                        "event_type": "format_error",
                        "message": "Output failed deterministic format validation.",
                    },
                    {
                        "step_index": 2,
                        "event_type": "final_output",
                        "output": "response=unstructured",
                    },
                ],
            }

        final_output = (
            str(expected_output)
            if force_expected_output and isinstance(expected_output, str)
            else f"[stub] answer for: {input_text[:50]}"
        )
        if should_answer_incorrect:
            final_output = f"[stub] incorrect answer for {dataset_item_id}"

        trace_events: list[dict[str, object]] = [
            {"step_index": 0, "event_type": "agent_start", "input": input_text},
        ]
        if should_include_tool_call:
            trace_events.append(
                {
                    "step_index": len(trace_events),
                    "event_type": "tool_call",
                    "tool_name": "document_lookup",
                    "input": {"query": input_text[:80]},
                    "output": {
                        "snippet": (
                            str(expected_output)[:80]
                            if isinstance(expected_output, str)
                            else input_text[:80]
                        )
                    },
                    "latency_ms": 37,
                    "status": "success",
                }
            )
        trace_events.append(
            {
                "step_index": len(trace_events),
                "event_type": "final_output",
                "output": final_output,
            }
        )
        return {
            "final_output": final_output,
            "latency_ms": 120,
            "token_usage": {"prompt": 100, "completion": 50},
            "cost": 0.001,
            "termination_reason": "answer_incorrect" if should_answer_incorrect else "completed",
            "error": None,
            "trace_events": trace_events,
        }
