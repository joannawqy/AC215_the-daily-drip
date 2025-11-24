"""Unit tests for index module."""
import os


class TestIndexModule:
    """Test the index module."""
    
    def test_index_file_exists(self):
        """Test that index.py exists."""
        index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'index.py')
        assert os.path.exists(index_path)
    
    def test_index_file_not_empty(self):
        """Test that index.py is not empty."""
        index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'index.py')
        with open(index_path, 'r') as f:
            content = f.read()
        assert len(content) > 0
    
    def test_index_has_chromadb_reference(self):
        """Test that index.py references ChromaDB."""
        index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'index.py')
        with open(index_path, 'r') as f:
            content = f.read()
        assert 'chroma' in content.lower()


class TestIndexConfiguration:
    """Test index configuration."""
    
    def test_indexes_directory_exists(self):
        """Test that indexes directory exists."""
        indexes_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'indexes')
        assert os.path.exists(indexes_path)
    
    def test_data_directory_exists(self):
        """Test that data directory exists."""
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        assert os.path.exists(data_path)
