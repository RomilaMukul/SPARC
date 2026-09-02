"""
Unit Tests for Telemetry Data Ingestion & Sanitization Pipeline
==============================================================
Tests clean_cdf_array filtering, fill value masking, and telemetry parsing logic.
"""

import pytest
import numpy as np
from src.data.ingest_aditya import clean_cdf_array


def test_clean_cdf_array_fill_value_masking():
    """Verify fill values (-1e31, NaN, Inf) are masked to np.nan."""
    raw_cdf_data = np.array([-1e31, 450.0, 520.0, np.nan, np.inf, 1e9, 380.0])
    cleaned = clean_cdf_array(raw_cdf_data, min_val=0.0, max_val=1e8)

    assert cleaned is not None
    assert np.isnan(cleaned[0]), "Fill value -1e31 must be masked to NaN"
    assert cleaned[1] == 450.0
    assert cleaned[2] == 520.0
    assert np.isnan(cleaned[3]), "Input NaN must remain NaN"
    assert np.isnan(cleaned[4]), "Input Inf must be masked to NaN"
    assert np.isnan(cleaned[5]), "Out of range max_val must be masked to NaN"
    assert cleaned[6] == 380.0


def test_clean_cdf_array_empty_input():
    """Verify handling of None input."""
    assert clean_cdf_array(None) is None
