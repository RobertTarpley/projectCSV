"""Test that pytest setup is working correctly."""

def test_basic_pytest_functionality():
    """Test that basic pytest functionality works."""
    assert 1 + 1 == 2
    assert "hello" == "hello"
    

def test_imports():
    """Test that we can import our modules."""
    import reader
    import validators
    import profiler
    import transformer
    
    # Just check they import without error
    assert reader is not None
    assert validators is not None
    assert profiler is not None
    assert transformer is not None