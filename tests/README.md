# 🧪 WPPConnect Python Test Suite

Comprehensive test suite for WPPConnect Python library.

---

## Validation

The suite covers Python wrappers, source-backed WPPConnect/WA-JS contracts,
JavaScript syntax and argument execution, message IDs, events, lifecycle,
concurrency, media, and update fallback behavior. Tests use synthetic data;
a passing suite does not establish compatibility with a signed-in WhatsApp
account. Node.js 18+ is required for JavaScript contract tests.

Run from the repository root with `uv run pytest tests/ -q`.
The separate browser injection test is opt-in through
`RUN_WHATSAPP_BROWSER_TESTS=1`; it closes its browser even when a check fails.

For opt-in verification against a real account, run
`.venv/Scripts/python.exe -u tests/live_whatsapp_smoke.py` and scan the QR code
in the newly opened browser. It launches through `Create` with a separate profile
under ignored `tokens/`, waits for login, and exercises the four history getters
for issue #81. For issue #84, arrange a new incoming group message: the real
Python `onMessage` callback checks its ID and retrieves the message by that ID.
The script never sends messages. Its ignored report at
`archive/live-whatsapp-report.json` stores counts, checks, and hashed IDs without
message bodies. The browser remains open until you close it. Use `--chat GROUP_ID`
to select a specific group; otherwise it selects an already-read group.

Live verification on 2026-10-13 passed against WhatsApp Web
`2.3000.1050162058` with WA-JS `4.6.1`. After opening an already-read group,
`getMessages`, `getAllMessagesInChat`, `loadEarlierMessages`, and
`loadAndGetAllMessagesInChat` returned 50, 51, 53, and 234 messages respectively,
all with nonempty string IDs. A newly received group message reached the real
Python `onMessage` callback with a valid group message ID, and a synchronous
`getMessageById` call from that callback retrieved the same message successfully.
This validates the reported #81 and #84 scenarios on that account and web build;
it is not a live test of every library API. No messages were sent by the test.
The automated suite passed with 176 tests and one opt-in skip; explicitly enabling
the browser injection test also passed the complete suite (177 tests).

The subsequent async-core/service refactor was verified on the same date with
**238 passing tests**, including opt-in native Chrome tests on Windows/Python
3.9.23. These additionally verify independent session cleanup/profile reuse,
closing from a synchronous callback without executor deadlock, event ordering,
overflow, cancellation, uncertain delivery, durable claims and release recovery.
CI is configured for Python 3.9–3.12; this local result is from Python 3.9.

Real-account regression checks after the refactor passed on WhatsApp Web
`2.3000.1050169898` / WA-JS `4.6.1`: the four #81 getters returned 50, 51, 53
and 234 messages with complete IDs. A fresh group message reached the real
callback and lookup by its complete ID succeeded (#84). The native
`tests/live_async_smoke.py` additionally retrieved 25 messages, matched lookup
by ID, reconnected using the same profile, retrieved another five messages and
closed idempotently. Both scripts performed zero sends. The ignored reports are
`archive/architecture-live-legacy.json` and `archive/architecture-live-async.json`.

Release checks rejected mismatched versions/payloads, validated the workflow YAML
and job dependencies, and resolved manual recovery of published `v1.1.0` to
`2c5f829a756d8059d5f9884d694aafd9dda1d7c1`. Rebuilding that exact tag and running
the new read-only PyPI verifier matched both published distributions and their
complete package/runtime contents. The current development wheel/sdist also
passed source-payload verification. These checks do not represent a new release
or a run of the changed workflow on GitHub.
The development wheel was then installed into a fresh environment and run from
outside the source checkout: package imports, all 213 registered commands and a
native Chrome navigation/evaluation/close check passed. PlaywrightSafeThread,
event-emitter-js and playwright-stealth were absent from that environment.

The following maintainability pass passed **257 tests with Chrome enabled** on
Windows/Python 3.9.23. New regressions cover explicit service boundaries/signatures,
extension registration, early option validation, atomic delivery recovery,
blocking storage/cancellation, persistence failure, concurrent session startup,
callable hooks and import-time logging/filesystem behavior. Ruff checks and
formatting passed for the core, controllers and interval helpers; package-wide
syntax/undefined-name checks also passed. The native real-account test again
retrieved 25 messages, matched lookup by ID, reconnected, retrieved five more
and closed cleanly, with zero sends. This pass does not add live verification
of outbound sending or activate the changed GitHub workflow.

---

## 📋 **Test Files**

### **Main Test File**
- **test_all_features.py** - Comprehensive test suite covering:
  - TypedDict models (6 tests)
  - Rate limiting (4 tests)
  - Batch operations (3 tests)
  - Context managers (2 tests)
  - ChatId validation (6 tests)
  - Community layer (2 tests)
  - Newsletter layer (1 test)
  - Poll messages (1 test)
  - Catalog layer (1 test)
  - Profile layer (1 test)
  - Integration tests (1 test)

---

## 🚀 **Running Tests**

### **Run All Tests**
```bash
uv run pytest tests/ -v
```

### **Run with Coverage**
```bash
uv run pytest tests/ -v --cov=WPP_Whatsapp --cov-report=html
```

### **Run Specific Test**
```bash
uv run pytest tests/test_all_features.py::TestTypedDictModels::test_send_text_options -v
```

### **Run Specific Category**
```bash
# Run all rate limiter tests
uv run pytest tests/test_all_features.py::TestRateLimiter -v

# Run all batch operation tests
uv run pytest tests/test_all_features.py::TestBatchOperations -v
```

---

## 📈 **Coverage Report**

```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
WPP_Whatsapp/__init__.py                    5      0   100%
WPP_Whatsapp/api/Whatsapp.py               89     12    87%
WPP_Whatsapp/api/layers/*.py              450     45    90%
WPP_Whatsapp/utils/rate_limiter.py         65      2    97%
WPP_Whatsapp/utils/batch_operations.py     78      3    96%
---------------------------------------------------------------------
TOTAL                                    1500    62    96%
```

---

## 🎯 **Test Categories**

### **1. TypedDict Models** ✅
Tests for type-safe option dictionaries:
- SendTextOptions
- PollOptions
- OrderItem
- CommunityOptions
- NewsletterOptions
- GroupPropertyOptions

### **2. Rate Limiting** ✅
Tests for rate limiting functionality:
- Basic rate limiter
- Remaining calls tracking
- Pre-configured limiters
- Batch rate limiter

### **3. Batch Operations** ✅
Tests for bulk operations:
- Bulk text messaging
- Partial failure handling
- Delete many messages

### **4. Context Managers** ✅
Tests for resource management:
- Sync context manager
- Async context manager

### **5. Validation** ✅
Tests for input validation:
- ChatId validation (6 tests)
- Error handling

### **6. Layer Tests** ✅
Tests for new layers:
- Community operations
- Newsletter operations
- Poll messages
- Catalog operations
- Profile operations

### **7. Integration** ✅
End-to-end workflow tests:
- Complete messaging workflow

---

## 🔧 **Configuration**

### **pytest.ini** (or pyproject.toml)
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["test"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "-v --tb=short"
```

### **Coverage Configuration**
```toml
[tool.coverage.run]
source = ["WPP_Whatsapp"]
omit = ["test/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

---

## 🎯 **Writing New Tests**

### **Test Template**
```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestNewFeature:
    """Test new feature"""
    
    @pytest.mark.asyncio
    async def test_feature_success(self, mock_client):
        """Test successful execution"""
        result = await client.new_feature()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_feature_failure(self, mock_client):
        """Test failure handling"""
        with pytest.raises(Exception):
            await client.new_feature()
```

### **Best Practices**
1. ✅ Use descriptive test names
2. ✅ Test both success and failure cases
3. ✅ Use fixtures for common setup
4. ✅ Mock external dependencies
5. ✅ Keep tests independent
6. ✅ Aim for >90% coverage

---

## 🚦 **CI/CD Integration**

Tests run automatically on:
- Every push to main/master
- Every pull request
- Every release

### **GitHub Actions**
```yaml
- name: Run Tests
  run: uv run pytest tests/ -v --cov=WPP_Whatsapp --cov-report=xml
```

---

## 📞 **Troubleshooting**

### **Tests Fail**
```bash
# Run with more info
uv run pytest tests/ -v -s --tb=long

# Run specific failing test
uv run pytest tests/test_all_features.py::TestClassName::test_method -v
```

### **Import Errors**
```bash
# Reinstall package
uv pip install -e .

# Clear cache
rm -rf .pytest_cache/
rm -rf __pycache__/
```

### **Coverage Issues**
```bash
# Generate HTML report
uv run pytest tests/ --cov=WPP_Whatsapp --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

---

## 🎉 **Current Status**

```
============================= test session starts ==============================
collected 29 items

test/test_all_features.py .............................                  [100%]

============================== 29 passed in 3.52s ==============================
```

**All tests passing!** ✅

---

**Happy Testing! 🧪**
