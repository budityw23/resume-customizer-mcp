"""
Tests for the logging utilities in resume_customizer.utils.logger.
"""

import logging
from pathlib import Path

import pytest

from resume_customizer.utils.logger import get_logger, setup_logger


class TestSetupLogger:
    """Tests for the setup_logger function."""

    def teardown_method(self):
        """Remove any test loggers to avoid cross-test pollution."""
        for name in list(logging.Logger.manager.loggerDict):
            if name.startswith("test_rc_"):
                logger = logging.getLogger(name)
                logger.handlers.clear()

    def test_returns_logger_instance(self):
        logger = setup_logger("test_rc_basic")
        assert isinstance(logger, logging.Logger)

    def test_logger_name(self):
        logger = setup_logger("test_rc_named")
        assert logger.name == "test_rc_named"

    def test_default_level_is_info(self):
        logger = setup_logger("test_rc_level_default")
        assert logger.level == logging.INFO

    def test_custom_level_debug(self):
        logger = setup_logger("test_rc_debug", level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_custom_level_warning(self):
        logger = setup_logger("test_rc_warn", level="WARNING")
        assert logger.level == logging.WARNING

    def test_custom_level_error(self):
        logger = setup_logger("test_rc_err", level="ERROR")
        assert logger.level == logging.ERROR

    def test_has_console_handler(self):
        logger = setup_logger("test_rc_console")
        assert len(logger.handlers) >= 1
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_duplicate_setup_returns_same_logger(self):
        """Calling setup_logger twice on same name should not add duplicate handlers."""
        logger1 = setup_logger("test_rc_dup")
        handler_count = len(logger1.handlers)
        logger2 = setup_logger("test_rc_dup")
        assert logger1 is logger2
        assert len(logger2.handlers) == handler_count

    def test_custom_format_string(self):
        fmt = "%(levelname)s - %(message)s"
        logger = setup_logger("test_rc_fmt", format_string=fmt)
        assert len(logger.handlers) >= 1
        assert logger.handlers[0].formatter._fmt == fmt

    def test_file_handler_created(self, tmp_path):
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_rc_file", log_file=log_file)
        handler_types = [type(h) for h in logger.handlers]
        assert logging.FileHandler in handler_types

    def test_file_handler_creates_parent_dirs(self, tmp_path):
        log_file = tmp_path / "subdir" / "nested" / "test.log"
        setup_logger("test_rc_nested_file", log_file=log_file)
        assert log_file.parent.exists()

    def test_file_handler_writes_log(self, tmp_path):
        log_file = tmp_path / "output.log"
        logger = setup_logger("test_rc_write", log_file=log_file)
        logger.info("hello from test")
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        assert log_file.exists()
        content = log_file.read_text()
        assert "hello from test" in content


class TestGetLogger:
    """Tests for the get_logger function."""

    def teardown_method(self):
        for name in list(logging.Logger.manager.loggerDict):
            if name.startswith("test_get_"):
                logger = logging.getLogger(name)
                logger.handlers.clear()

    def test_returns_logger(self):
        logger = get_logger("test_get_basic")
        assert isinstance(logger, logging.Logger)

    def test_logger_has_handlers(self):
        logger = get_logger("test_get_handlers")
        assert len(logger.handlers) >= 1

    def test_same_name_returns_same_logger(self):
        logger1 = get_logger("test_get_same")
        logger2 = get_logger("test_get_same")
        assert logger1 is logger2

    def test_default_name(self):
        logger = get_logger()
        assert logger.name == "resume_customizer"

    def test_already_configured_logger_not_reconfigured(self):
        """If logger already has handlers, get_logger should not add more."""
        logger = get_logger("test_get_existing")
        handler_count_after_first = len(logger.handlers)
        logger2 = get_logger("test_get_existing")
        assert len(logger2.handlers) == handler_count_after_first
