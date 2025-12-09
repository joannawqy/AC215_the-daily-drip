"""Unit tests for chunk module."""
import json
import sys
from src.chunk import main


class TestChunkModule:
    """Test the chunk module functionality."""
    
    def test_chunk_basic_functionality(self, monkeypatch, tmp_path):
        """Test basic chunking functionality."""
        # Create test input file
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"
        
        # Write test data
        test_record = {
            "id": "test1",
            "text": "A" * 1000,  # Long text to be chunked
            "meta": {"source": "test"}
        }
        
        with open(input_file, 'w') as f:
            f.write(json.dumps(test_record) + "\n")
        
        # Mock command line arguments
        test_args = [
            'chunk.py',
            '--records', str(input_file),
            '--out', str(output_file),
            '--max_chars', '400'
        ]
        monkeypatch.setattr(sys, 'argv', test_args)
        
        # Run the main function
        main()
        
        # Verify output
        assert output_file.exists()
        
        # Read and verify chunks
        with open(output_file) as f:
            chunks = [json.loads(line) for line in f]
        
        # Should have multiple chunks since text is 1000 chars and max is 400
        assert len(chunks) > 1
        
        # Each chunk should have required fields
        for chunk in chunks:
            assert "id" in chunk
            assert "text" in chunk
            assert "meta" in chunk
            assert len(chunk["text"]) <= 400
    
    def test_chunk_preserves_metadata(self, monkeypatch, tmp_path):
        """Test that chunking preserves metadata."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"
        
        test_meta = {"bean": "Ethiopian", "roast": "Light"}
        test_record = {
            "id": "test2",
            "text": "Short text",
            "meta": test_meta
        }
        
        with open(input_file, 'w') as f:
            f.write(json.dumps(test_record) + "\n")
        
        test_args = [
            'chunk.py',
            '--records', str(input_file),
            '--out', str(output_file)
        ]
        monkeypatch.setattr(sys, 'argv', test_args)
        
        main()
        
        with open(output_file) as f:
            chunk = json.loads(f.readline())
        
        assert chunk["meta"] == test_meta
    
    def test_chunk_short_text(self, monkeypatch, tmp_path):
        """Test chunking text shorter than max_chars."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"
        
        test_record = {
            "id": "test3",
            "text": "Short",
            "meta": {}
        }
        
        with open(input_file, 'w') as f:
            f.write(json.dumps(test_record) + "\n")
        
        test_args = [
            'chunk.py',
            '--records', str(input_file),
            '--out', str(output_file),
            '--max_chars', '100'
        ]
        monkeypatch.setattr(sys, 'argv', test_args)
        
        main()
        
        with open(output_file) as f:
            chunks = [json.loads(line) for line in f]
        
        # Short text should result in single chunk
        assert len(chunks) == 1
        assert chunks[0]["text"] == "Short"
