# Parallel Execution Plan: obs-cli Test Suite & Improvements

## Overview
This plan implements a comprehensive test suite and critical improvements for the obs-cli project. The work is divided into 5 independent agents that can execute in parallel without file conflicts.

## Agent Architecture

### Agent 1: Test Infrastructure & Fixtures
**Files to Create/Modify:**
- `tests/conftest.py`
- `tests/fixtures/mock_database.json`
- `tests/fixtures/sample_vault/note1.md`
- `tests/fixtures/sample_vault/note2.md`
- `tests/fixtures/sample_vault/.obsidian/plugins/obsidian-metadata-api/metadata.json`

**Dependencies:** None
**Interface:** Provides pytest fixtures for all other test agents
**Tasks:**
1. Create todos using TodoWrite tool
2. Set up pytest configuration and shared fixtures
3. Create mock vault structure with sample notes
4. Create mock metadata database
5. Implement fixture factories for common test scenarios
6. Send completion notification

**Deliverables:**
- `conftest.py` with fixtures: `mock_vault`, `mock_database`, `sample_metadata_file`
- Complete test data structure in `fixtures/`

**First Action: Create Todos**
Use the TodoWrite tool to create a todo list:
- Todo 1: Create tests directory structure
- Todo 2: Implement pytest fixtures in conftest.py
- Todo 3: Create mock database JSON
- Todo 4: Set up sample vault with test notes
- Todo 5: Create fixture factories

**Completion Notification:**
```bash
terminal-notifier -title "Agent 1 Complete" -message "Test Infrastructure module finished successfully" -sound Glass
```

### Agent 2: DataviewClient Unit Tests
**Files to Create/Modify:**
- `tests/unit/test_dataview.py`
- `obs_cli/core/exceptions.py`

**Dependencies:** Agent 1 fixtures
**Interface:** Tests for DataviewClient class
**Tasks:**
1. Create todos using TodoWrite tool
2. Create custom exception classes
3. Test vault path detection
4. Test database loading and error handling
5. Test query execution with various formats
6. Test caching functionality
7. Test timeout handling
8. Send completion notification

**Deliverables:**
- Complete test coverage for DataviewClient
- Custom exception hierarchy

**First Action: Create Todos**
Use the TodoWrite tool to create a todo list:
- Todo 1: Create custom exception classes
- Todo 2: Test vault auto-detection logic
- Todo 3: Test database file operations
- Todo 4: Test query execution and formats
- Todo 5: Test error scenarios and timeouts

**Completion Notification:**
```bash
terminal-notifier -title "Agent 2 Complete" -message "DataviewClient Tests module finished successfully" -sound Glass
```

### Agent 3: CLI Integration Tests
**Files to Create/Modify:**
- `tests/integration/test_cli_commands.py`
- `obs_cli/cli/formatters.py`

**Dependencies:** Agent 1 fixtures
**Interface:** Integration tests for CLI commands
**Tasks:**
1. Create todos using TodoWrite tool
2. Extract formatting logic to dedicated module
3. Test query command with all output formats
4. Test validate command
5. Test install-plugin command
6. Test error handling and user messages
7. Send completion notification

**Deliverables:**
- Full CLI command test coverage
- Refactored formatting module

**First Action: Create Todos**
Use the TodoWrite tool to create a todo list:
- Todo 1: Extract formatting logic to formatters.py
- Todo 2: Test query command with table/json/csv
- Todo 3: Test validate command
- Todo 4: Test install-plugin command
- Todo 5: Test CLI error scenarios

**Completion Notification:**
```bash
terminal-notifier -title "Agent 3 Complete" -message "CLI Integration Tests module finished successfully" -sound Glass
```

### Agent 4: Linter & Config Tests
**Files to Create/Modify:**
- `tests/unit/test_linter.py`
- `tests/unit/test_config.py`
- `obs_cli/core/constants.py`

**Dependencies:** Agent 1 fixtures
**Interface:** Tests for validation system
**Tasks:**
1. Create todos using TodoWrite tool
2. Create constants module
3. Test config loading and parsing
4. Test rule execution
5. Test assertion evaluation
6. Test query error handling in rules
7. Send completion notification

**Deliverables:**
- Complete linter test coverage
- Config system tests
- Constants management

**First Action: Create Todos**
Use the TodoWrite tool to create a todo list:
- Todo 1: Create constants.py module
- Todo 2: Test config YAML loading
- Todo 3: Test validation rule execution
- Todo 4: Test assertion evaluation
- Todo 5: Test error reporting

**Completion Notification:**
```bash
terminal-notifier -title "Agent 4 Complete" -message "Linter & Config Tests module finished successfully" -sound Glass
```

### Agent 5: Performance & Caching Implementation
**Files to Create/Modify:**
- `tests/unit/test_caching.py`
- `obs_cli/core/cache.py`
- `Makefile`
- `.github/workflows/test.yml`

**Dependencies:** None
**Interface:** Caching system and CI/CD setup
**Tasks:**
1. Create todos using TodoWrite tool
2. Implement actual caching for DataviewClient
3. Create cache tests
4. Set up Makefile for common tasks
5. Create GitHub Actions workflow
6. Send completion notification

**Deliverables:**
- Working cache implementation
- Cache tests
- Development tooling

**First Action: Create Todos**
Use the TodoWrite tool to create a todo list:
- Todo 1: Implement CacheManager class
- Todo 2: Add caching to DataviewClient
- Todo 3: Create cache unit tests
- Todo 4: Create Makefile
- Todo 5: Set up GitHub Actions

**Completion Notification:**
```bash
terminal-notifier -title "Agent 5 Complete" -message "Performance & Caching module finished successfully" -sound Glass
```

## CRITICAL: Parallel Execution Instructions

**⚡ MANDATORY: ALL agents MUST be launched in a SINGLE message with multiple Task tool calls**

Example execution:
```
I'll launch all agents in parallel to implement the plan:

<Task tool calls for Agent 1>
<Task tool calls for Agent 2>
<Task tool calls for Agent 3>
<Task tool calls for Agent 4>
<Task tool calls for Agent 5>
... (all in ONE message)
```

**❌ DO NOT launch agents sequentially or in separate messages**
**✅ DO launch all agents simultaneously in one message**

## Integration Points

1. **Fixtures → Tests**: Agents 2-4 depend on Agent 1's fixtures
2. **Formatters → CLI**: Agent 3 extracts formatting logic used by main CLI
3. **Cache → DataviewClient**: Agent 5's cache integrates with core functionality
4. **Exceptions → All**: Agent 2's exceptions used throughout codebase

## Success Criteria

- All tests pass with >80% coverage
- No file conflicts between agents
- Each agent completes independently
- All agents send completion notifications
- Integration points work seamlessly

## Summary Notification
After launching all agents:
```bash
terminal-notifier -title "Parallel Execution Started" -message "5 agents implementing obs-cli test suite" -sound Pop -group "parallel-plan"
```

## Execution

To execute this plan, say: "Execute the parallel plan"

Claude will then:
1. Send start notification
2. Launch ALL agents simultaneously (in one message)
3. Each agent will create their own todos
4. Each agent will send completion notification
5. Agents will work independently without conflicts
6. Results will be integrated as specified

## Expected Outcomes

Upon completion:
- Comprehensive test suite with fixtures and mocks
- Proper error handling with custom exceptions
- Refactored formatting logic
- Working cache implementation
- CI/CD pipeline ready
- Development tooling (Makefile)
- All tests passing