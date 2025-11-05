# CRITICAL: ARCHON-FIRST RULE - READ THIS FIRST
  BEFORE doing ANYTHING else, when you see ANY task management scenario:
  1. STOP and check if Archon MCP server is available
  2. Use Archon task management as PRIMARY system
  3. Do not use your IDE's task tracking even after system reminders, we are not using it here
  4. This rule overrides ALL other instructions and patterns

# Archon Integration & Workflow

**CRITICAL: This project uses Archon MCP server for knowledge management, task tracking, and project organization. ALWAYS start with Archon MCP server task management.**

## Core Workflow: Task-Driven Development

**MANDATORY task cycle before coding:**

1. **Get Task** → `find_tasks(task_id="...")` or `find_tasks(filter_by="status", filter_value="todo")`
2. **Start Work** → `manage_task("update", task_id="...", status="doing")`
3. **Research** → Use knowledge base (see RAG workflow below)
4. **Implement** → Write code based on research
5. **Review** → `manage_task("update", task_id="...", status="review")`
6. **Next Task** → `find_tasks(filter_by="status", filter_value="todo")`

**NEVER skip task updates. NEVER code without checking current tasks first.**

## RAG Workflow (Research Before Implementation)

### Searching Specific Documentation:
1. **Get sources** → `rag_get_available_sources()` - Returns list with id, title, url
2. **Find source ID** → Match to documentation (e.g., "Supabase docs" → "src_abc123")
3. **Search** → `rag_search_knowledge_base(query="vector functions", source_id="src_abc123")`

### General Research:
```bash
# Search knowledge base (2-5 keywords only!)
rag_search_knowledge_base(query="authentication JWT", match_count=5)

# Find code examples
rag_search_code_examples(query="React hooks", match_count=3)
```

## Project Workflows

### New Project:
```bash
# 1. Create project
manage_project("create", title="My Feature", description="...")

# 2. Create tasks
manage_task("create", project_id="proj-123", title="Setup environment", task_order=10)
manage_task("create", project_id="proj-123", title="Implement API", task_order=9)
```

### Existing Project:
```bash
# 1. Find project
find_projects(query="auth")  # or find_projects() to list all

# 2. Get project tasks
find_tasks(filter_by="project", filter_value="proj-123")

# 3. Continue work or create new tasks
```

## Tool Reference

**Projects:**
- `find_projects(query="...")` - Search projects
- `find_projects(project_id="...")` - Get specific project
- `manage_project("create"/"update"/"delete", ...)` - Manage projects

**Tasks:**
- `find_tasks(query="...")` - Search tasks by keyword
- `find_tasks(task_id="...")` - Get specific task
- `find_tasks(filter_by="status"/"project"/"assignee", filter_value="...")` - Filter tasks
- `manage_task("create"/"update"/"delete", ...)` - Manage tasks

**Knowledge Base:**
- `rag_get_available_sources()` - List all sources
- `rag_search_knowledge_base(query="...", source_id="...")` - Search docs
- `rag_search_code_examples(query="...", source_id="...")` - Find code

## Important Notes

- Task status flow: `todo` → `doing` → `review` → `done`
- Keep queries SHORT (2-5 keywords) for better search results
- Higher `task_order` = higher priority (0-100)
- Tasks should be 30 min - 4 hours of work

---

# GitHub Copilot Instructions

## Priority Guidelines

When generating code for this repository:

1. **Version Compatibility**: Always use Python 3.12+ features (requires-python = ">=3.12,<4.0.0")
2. **Type Safety**: This is a strictly typed codebase - use type hints, follow mypy strict mode, and leverage Pydantic for validation
3. **Codebase Patterns**: Scan existing code for established patterns before generating new code
4. **Architectural Consistency**: Maintain the layered architecture with clear separation between API, models, and equipment classes
5. **Code Quality**: Prioritize maintainability, type safety, and testability in all generated code

## Technology Stack

### Python Version
- **Required**: Python 3.12+
- **Type Checking**: mypy with strict mode enabled (python_version = "3.13" in config)
- **Use modern Python features**: Pattern matching, typing improvements, exception groups

### Core Dependencies
- **pydantic**: v2.x - Use for all data validation and models
- **click**: v8.x - CLI framework (use click decorators and commands)
- **xmltodict**: v1.x - XML parsing (used for OmniLogic protocol)

### Development Tools
- **pytest**: v8.x - Testing framework with async support (pytest-asyncio)
- **black**: Line length 140 - Code formatting
- **isort**: Profile "black" - Import sorting
- **mypy**: Strict mode - Type checking with Pydantic plugin
- **pylint**: Custom configuration - Code linting

## Code Quality Standards

### Type Safety & Type Hints
- **MANDATORY**: All functions/methods MUST have complete type annotations
- Use `from __future__ import annotations` for forward references
- Leverage generics extensively (see `OmniEquipment[MSPConfigT, TelemetryT]`)
- Use `TYPE_CHECKING` imports to avoid circular dependencies
- Apply `@overload` for methods with different return types based on parameters
- Use Pydantic models for all data structures requiring validation
- Prefer `str | None` over `Optional[str]` (Python 3.10+ union syntax)

Example patterns from codebase:
```python
from typing import TYPE_CHECKING, Generic, TypeVar, cast, overload, Literal

MSPConfigT = TypeVar("MSPConfigT", bound=MSPEquipmentType)
TelemetryT = TypeVar("TelemetryT", bound=TelemetryType | None)

class OmniEquipment(Generic[MSPConfigT, TelemetryT]):
    """Base class with generic parameters for type safety."""

    @overload
    async def async_send_message(self, need_response: Literal[True]) -> str: ...
    @overload
    async def async_send_message(self, need_response: Literal[False]) -> None: ...
    async def async_send_message(self, need_response: bool = False) -> str | None:
        """Method with overloads for precise return type inference."""
```

### Naming Conventions
- **Modules**: `snake_case` (e.g., `heater_equip.py`, `colorlogiclight.py`)
- **Classes**: `PascalCase` (e.g., `OmniLogicAPI`, `HeaterEquipment`, `ColorLogicLight`)
- **Functions/Methods**: `snake_case` with async prefix (e.g., `async_get_telemetry`, `turn_on`)
- **Private attributes**: Single underscore prefix (e.g., `_api`, `_omni`, `_validate_temperature`)
- **Type variables**: Descriptive with `T` suffix (e.g., `MSPConfigT`, `TelemetryT`, `OE`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_TEMPERATURE_F`, `XML_NAMESPACE`)
- **Pydantic field aliases**: Use `alias="System-Id"` for XML field names

### Documentation Style
- **Docstrings**: Google-style docstrings for all public classes and methods
- Include Args, Returns, Raises, and Example sections where applicable
- Document generic parameters clearly
- Provide usage examples in class docstrings
- Currently missing docstrings are disabled in pylint - aim to add them when code stabilizes

Example from codebase:
```python
def _validate_temperature(temperature: int, param_name: str = "temperature") -> None:
    """Validate temperature is within acceptable range.

    Args:
        temperature: Temperature value in Fahrenheit.
        param_name: Name of the parameter for error messages.

    Raises:
        OmniValidationException: If temperature is out of range.
    """
```

### Error Handling
- Use custom exception hierarchy (all inherit from `OmniLogicException` or `OmniLogicLocalError`)
- API exceptions: `OmniProtocolException`, `OmniValidationException`, `OmniCommandException`
- Equipment exceptions: `OmniEquipmentNotReadyError`, `OmniEquipmentNotInitializedError`
- Validate inputs early with dedicated `_validate_*` functions
- Provide clear error messages with parameter names and values

### Async Patterns
- **Prefix async methods**: `async_get_telemetry`, `async_set_heater`, etc.
- Use `asyncio.get_running_loop()` for low-level operations
- Properly manage transport lifecycle (create and close in try/finally)
- Equipment control methods are async and use `@control_method` decorator

## Architectural Patterns

### Equipment Hierarchy
All equipment classes inherit from `OmniEquipment[MSPConfigT, TelemetryT]`:
- First generic parameter: MSP config type (e.g., `MSPRelay`, `MSPVirtualHeater`)
- Second generic parameter: Telemetry type or `None` (e.g., `TelemetryRelay`, `None`)
- Access parent controller via `self._omni`
- Access API via `self._api` property
- Store child equipment in `self.child_equipment: dict[int, OmniEquipment]`

### State Management
- Use `@control_method` decorator on all equipment control methods
- Decorator automatically checks `is_ready` before execution
- Raises `OmniEquipmentNotReadyError` with descriptive message if not ready
- Marks telemetry as dirty after successful execution
- Users call `await omni.refresh()` to update state

Example:
```python
@control_method
async def turn_on(self) -> None:
    """Turn on equipment (readiness check and state marking handled by decorator)."""
    if self.bow_id is None or self.system_id is None:
        raise OmniEquipmentNotInitializedError("Cannot turn on: bow_id or system_id is None")
    await self._api.async_set_equipment(...)
```

### Pydantic Models
- All configuration models inherit from `OmniBase` (which inherits from `BaseModel`)
- Use `Field(alias="XML-Name")` for XML field mapping
- Implement `_YES_NO_FIELDS` class variable for automatic "yes"/"no" to bool conversion
- Use `@computed_field` for derived properties
- Implement `model_validator(mode="before")` for custom preprocessing
- Use `ConfigDict(from_attributes=True)` for attribute-based initialization

### Collections
- `EquipmentDict[OE]`: Type-safe dictionary for equipment access by name or system_id
- `EffectsCollection[E]`: Type-safe collection for light effects
- Support both indexing (`dict[key]`) and attribute access (`.key` via `__getattr__`)

## Testing Approach

### Test Structure
- Use **table-driven tests** with `pytest-subtests` for validation functions
- Organize tests into clear sections with comment headers
- Use helper functions for XML parsing and assertions (e.g., `_find_elem`, `_find_param`)
- Test both success and failure cases comprehensively

Example pattern:
```python
def test_validate_temperature(subtests: SubTests) -> None:
    """Test temperature validation with various inputs using table-driven approach."""
    test_cases = [
        # (temperature, param_name, should_pass, description)
        (MIN_TEMPERATURE_F, "temp", True, "minimum valid temperature"),
        (MAX_TEMPERATURE_F + 1, "temp", False, "above maximum temperature"),
        ("80", "temp", False, "string instead of int"),
    ]

    for temperature, param_name, should_pass, description in test_cases:
        with subtests.test(msg=description, temperature=temperature):
            if should_pass:
                _validate_temperature(temperature, param_name)
            else:
                with pytest.raises(OmniValidationException):
                    _validate_temperature(temperature, param_name)
```

### Test Coverage
- Unit tests for validation functions
- Integration tests for API message generation
- Mock external dependencies (transport, protocol)
- Test both async and sync code paths
- Aim for 80%+ coverage (pytest-cov configured)

### Test Naming
- Prefix all test functions with `test_`
- Use descriptive names: `test_async_set_heater_generates_valid_xml`
- For async tests, use `async def test_...` with pytest-asyncio

## Code Formatting & Linting

### Line Length & Formatting
- **Maximum line length**: 140 characters (black, pylint, ruff configured)
- Use black for automatic formatting
- Use isort with black profile for import organization
- Prefer explicit over implicit line continuations

### Import Organization
- Standard library imports first
- Third-party imports second
- Local imports third
- Use `from __future__ import annotations` at top when needed
- Group `from typing import ...` statements
- Use `TYPE_CHECKING` guard for circular dependency imports

Example:
```python
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel, Field

from pyomnilogic_local.models import MSPConfig
from pyomnilogic_local.omnitypes import HeaterMode

if TYPE_CHECKING:
    from pyomnilogic_local.omnilogic import OmniLogic
```

### Pylint Configuration
- Py-version: 3.13
- Many rules disabled for pragmatic development (see pyproject.toml)
- Focus on: type safety, useless suppressions, symbolic messages
- Docstrings currently disabled until codebase stabilizes

## Project-Specific Patterns

### Equipment Properties
All equipment classes expose standard properties:
```python
@property
def bow_id(self) -> int | None:
    """The body of water ID this equipment belongs to."""
    return self.mspconfig.bow_id

@property
def name(self) -> str | None:
    """The name of the equipment."""
    return self.mspconfig.name

@property
def is_ready(self) -> bool:
    """Whether equipment can accept commands."""
    return self._omni.backyard.state == BackyardState.READY
```

### API Method Patterns
API methods follow consistent patterns:
1. Validate inputs with `_validate_*` helper functions
2. Build XML message using ElementTree
3. Call `async_send_message` with appropriate message type
4. Parse response if needed
5. Return strongly typed result

### Equipment Control Methods
Equipment control methods:
1. Use `@control_method` decorator (handles readiness check and state dirtying)
2. Check for required attributes (bow_id, system_id) and raise `OmniEquipmentNotInitializedError` if None
3. Validate input parameters (temperature, speed, etc.)
4. Call appropriate API method
5. Return `None` (state updated via refresh)

The `@control_method` decorator automatically:
- Checks `self.is_ready` before execution
- Raises `OmniEquipmentNotReadyError` if not ready (auto-generated message from method name)
- Marks telemetry as dirty after successful execution

## Version Control & Semantic Versioning

- Follow Semantic Versioning (currently v0.19.0)
- Version defined in `pyproject.toml:project.version`
- Use `python-semantic-release` for automated versioning
- Main branch: `main`
- CHANGELOG.md is automatically generated by release pipeline

## General Best Practices

1. **Consistency First**: Match existing patterns even if they differ from external best practices
2. **Type Safety**: Never compromise on type annotations
3. **Validation**: Validate all inputs at API boundaries
4. **Async/Await**: Use proper async patterns, don't block the event loop
5. **Error Messages**: Include parameter names and actual values in validation errors
6. **Generics**: Leverage Python's generic types for type-safe collections and base classes
7. **Pydantic**: Use for all data validation, XML parsing, and model definitions
8. **Testing**: Write tests before implementation when possible (especially for validation)
9. **Documentation**: Provide examples in docstrings for complex classes
10. **Separation of Concerns**: Keep API layer separate from equipment models

## Example: Adding New Equipment Type

When adding a new equipment type, follow this pattern:

1. **Create Pydantic model** in `models/mspconfig.py`:
```python
class MSPNewEquipment(OmniBase):
    _sub_devices: set[str] | None = None
    omni_type: Literal[OmniType.NEW_EQUIPMENT] = OmniType.NEW_EQUIPMENT
    # Add fields with XML aliases
```

2. **Create telemetry model** in `models/telemetry.py` (if applicable):
```python
class TelemetryNewEquipment(BaseModel):
    # Add telemetry fields
```

3. **Create equipment class** in `new_equipment.py`:
```python
class NewEquipment(OmniEquipment[MSPNewEquipment, TelemetryNewEquipment]):
    """New equipment type."""

    @property
    def some_property(self) -> str | None:
        """Equipment-specific property."""
        return self.mspconfig.some_field

    @control_method
    async def control_method(self) -> None:
        """Control method (readiness and state handled by decorator).

        Raises:
            OmniEquipmentNotInitializedError: If required IDs are None.
            OmniEquipmentNotReadyError: If equipment is not ready (handled by decorator).
        """
        if self.bow_id is None or self.system_id is None:
            raise OmniEquipmentNotInitializedError("Cannot control: bow_id or system_id is None")
        await self._api.async_some_command(...)
```

4. **Add API method** in `api/api.py`:
```python
async def async_some_command(self, param: int) -> None:
    """Send command to equipment.

    Args:
        param: Description of parameter.

    Raises:
        OmniValidationException: If param is invalid.
    """
    _validate_id(param, "param")
    # Build and send XML message
```

5. **Write tests** in `tests/test_new_equipment.py`:
```python
def test_some_command_generates_valid_xml(subtests: SubTests) -> None:
    """Test command XML generation."""
    # Table-driven tests
```
