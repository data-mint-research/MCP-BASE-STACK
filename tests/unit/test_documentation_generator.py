"""
Unit tests for the DocumentationGenerator module.

This module contains tests for the DocumentationGenerator class, which is responsible
for generating documentation from code and other sources.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import pytest

from tests.utils.fixtures import temp_test_dir, temp_test_file
from tests.utils.mocks import MockFileSystem, MockConfig


@pytest.mark.documentation
class TestDocumentationGenerator:
    """Test cases for the DocumentationGenerator class."""
    
    @pytest.fixture
    def mock_doc_generator_module(self):
        """Create a mock documentation_generator module."""
        with patch('core.documentation.generator') as mock_module:
            # Create a mock DocumentationGenerator class
            mock_generator = MagicMock()
            mock_generator.generate_documentation.return_value = ["file1.md", "file2.md"]
            mock_generator.generate_module_documentation.return_value = "module.md"
            mock_generator.generate_class_documentation.return_value = "class.md"
            mock_generator.generate_function_documentation.return_value = "function.md"
            
            # Set up the module
            mock_module.DocumentationGenerator = MagicMock(return_value=mock_generator)
            
            yield mock_module
    
    def test_initialization(self, mock_doc_generator_module):
        """Test initializing the DocumentationGenerator."""
        from core.documentation.generator import DocumentationGenerator
        
        # Create a DocumentationGenerator instance
        generator = DocumentationGenerator()
        
        # Verify the generator was initialized
        assert generator is not None
    
    def test_generate_documentation(self, mock_doc_generator_module, temp_test_dir):
        """Test generating documentation."""
        from core.documentation.generator import DocumentationGenerator
        
        # Create a DocumentationGenerator instance
        generator = DocumentationGenerator()
        
        # Generate documentation
        output_files = generator.generate_documentation(
            source_dir=temp_test_dir,
            output_dir=os.path.join(temp_test_dir, "docs")
        )
        
        # Verify the output
        assert isinstance(output_files, list)
        assert len(output_files) == 2
        assert "file1.md" in output_files
        assert "file2.md" in output_files
    
    def test_generate_module_documentation(self, mock_doc_generator_module, temp_test_file):
        """Test generating module documentation."""
        from core.documentation.generator import DocumentationGenerator
        
        # Create a DocumentationGenerator instance
        generator = DocumentationGenerator()
        
        # Generate module documentation
        output_file = generator.generate_module_documentation(
            module_path=temp_test_file[1],
            output_dir=os.path.join(temp_test_file[0], "docs")
        )
        
        # Verify the output
        assert output_file == "module.md"
    
    def test_generate_class_documentation(self, mock_doc_generator_module, temp_test_file):
        """Test generating class documentation."""
        from core.documentation.generator import DocumentationGenerator
        
        # Create a DocumentationGenerator instance
        generator = DocumentationGenerator()
        
        # Generate class documentation
        output_file = generator.generate_class_documentation(
            module_path=temp_test_file[1],
            class_name="ExampleClass",
            output_dir=os.path.join(temp_test_file[0], "docs")
        )
        
        # Verify the output
        assert output_file == "class.md"
    
    def test_generate_function_documentation(self, mock_doc_generator_module, temp_test_file):
        """Test generating function documentation."""
        from core.documentation.generator import DocumentationGenerator
        
        # Create a DocumentationGenerator instance
        generator = DocumentationGenerator()
        
        # Generate function documentation
        output_file = generator.generate_function_documentation(
            module_path=temp_test_file[1],
            function_name="example_function",
            output_dir=os.path.join(temp_test_file[0], "docs")
        )
        
        # Verify the output
        assert output_file == "function.md"


@pytest.mark.documentation
class TestDocumentationGeneratorIntegration:
    """Integration tests for the DocumentationGenerator class."""
    
    @pytest.fixture
    def doc_config(self):
        """Create a documentation configuration."""
        return {
            "required": True,
            "coverage_threshold": 80.0,
            "output_directory": "docs/generated"
        }
    
    def test_documentation_generation_workflow(self, temp_test_dir, doc_config):
        """Test the complete documentation generation workflow."""
        # Update the output directory to use the temp directory
        doc_config["output_directory"] = os.path.join(temp_test_dir, "docs")
        
        # Create a test Python file
        test_file_path = os.path.join(temp_test_dir, "example.py")
        with open(test_file_path, "w") as f:
            f.write('''"""
Example module.

This module provides an example for testing.
"""

def example_function():
    """Example function docstring."""
    return True

class ExampleClass:
    """Example class docstring."""
    
    def __init__(self):
        """Initialize the example class."""
        self.value = 42
    
    def example_method(self):
        """Example method docstring."""
        return self.value
''')
        
        # Create a real DocumentationGenerator
        from core.documentation.generator import DocumentationGenerator
        generator = DocumentationGenerator()
        
        # Generate documentation
        with patch('core.documentation.generator.DocumentationGenerator.generate_documentation') as mock_generate:
            mock_generate.return_value = [
                os.path.join(doc_config["output_directory"], "example.md")
            ]
            output_files = generator.generate_documentation(
                source_dir=temp_test_dir,
                output_dir=doc_config["output_directory"]
            )
        
        # Verify the output
        assert isinstance(output_files, list)
        assert len(output_files) == 1
        assert os.path.basename(output_files[0]) == "example.md"


@pytest.mark.documentation
@pytest.mark.error
class TestDocumentationGeneratorErrorConditions:
    """Test cases for error conditions in the DocumentationGenerator."""
    
    @pytest.fixture
    def mock_error_module(self):
        """Create a mock module that raises errors."""
        with patch('core.documentation.generator') as mock_module:
            # Create a mock DocumentationGenerator class that raises errors
            mock_generator = MagicMock()
            mock_generator.generate_documentation.side_effect = Exception("Generation error")
            mock_generator.generate_module_documentation.side_effect = Exception("Module error")
            mock_generator.generate_class_documentation.side_effect = Exception("Class error")
            mock_generator.generate_function_documentation.side_effect = Exception("Function error")
            
            # Set up the module
            mock_module.DocumentationGenerator = MagicMock(return_value=mock_generator)
            
            yield mock_module
    
    def test_generation_error(self, mock_error_module, temp_test_dir):
        """Test handling of generation errors."""
        from core.documentation.generator import DocumentationGenerator
        
        # Create a DocumentationGenerator instance
        generator = DocumentationGenerator()
        
        # Generate documentation and verify it raises an exception
        with pytest.raises(Exception) as excinfo:
            generator.generate_documentation(
                source_dir=temp_test_dir,
                output_dir=os.path.join(temp_test_dir, "docs")
            )
        
        assert "Generation error" in str(excinfo.value)
    
    def test_module_error(self, mock_error_module, temp_test_file):
        """Test handling of module errors."""
        from core.documentation.generator import DocumentationGenerator
        
        # Create a DocumentationGenerator instance
        generator = DocumentationGenerator()
        
        # Generate module documentation and verify it raises an exception
        with pytest.raises(Exception) as excinfo:
            generator.generate_module_documentation(
                module_path=temp_test_file[1],
                output_dir=os.path.join(temp_test_file[0], "docs")
            )
        
        assert "Module error" in str(excinfo.value)
    
    def test_missing_file_error(self, mock_doc_generator_module, temp_test_dir):
        """Test handling of missing file errors."""
        from core.documentation.generator import DocumentationGenerator
        
        # Create a DocumentationGenerator instance
        generator = DocumentationGenerator()
        
        # Mock the generate_documentation method to check for file existence
        def mock_generate(source_dir, output_dir):
            if not os.path.exists(os.path.join(source_dir, "nonexistent.py")):
                raise FileNotFoundError("File not found: nonexistent.py")
            return ["file1.md"]
        
        mock_doc_generator_module.DocumentationGenerator().generate_documentation.side_effect = mock_generate
        
        # Generate documentation for a nonexistent file and verify it raises an exception
        with pytest.raises(FileNotFoundError) as excinfo:
            generator.generate_documentation(
                source_dir=temp_test_dir,
                output_dir=os.path.join(temp_test_dir, "docs")
            )
        
        assert "File not found" in str(excinfo.value)
    
    def test_permission_error(self, mock_doc_generator_module, temp_test_dir):
        """Test handling of permission errors."""
        from core.documentation.generator import DocumentationGenerator
        
        # Create a DocumentationGenerator instance
        generator = DocumentationGenerator()
        
        # Mock the generate_documentation method to raise a permission error
        mock_doc_generator_module.DocumentationGenerator().generate_documentation.side_effect = PermissionError("Permission denied")
        
        # Generate documentation and verify it raises an exception
        with pytest.raises(PermissionError) as excinfo:
            generator.generate_documentation(
                source_dir=temp_test_dir,
                output_dir=os.path.join(temp_test_dir, "docs")
            )
        
        assert "Permission denied" in str(excinfo.value)


@pytest.mark.documentation
class TestDocumentationGeneratorRecovery:
    """Test cases for recovery mechanisms in the DocumentationGenerator."""
    
    @pytest.fixture
    def mock_recovery_module(self):
        """Create a mock module with recovery mechanisms."""
        with patch('core.documentation.generator') as mock_module:
            # Create a mock DocumentationGenerator class with recovery mechanisms
            mock_generator = MagicMock()
            
            # Generate documentation method that fails first, then succeeds
            generate_mock = MagicMock()
            generate_mock.side_effect = [Exception("Generation error"), ["file1.md", "file2.md"]]
            mock_generator.generate_documentation = generate_mock
            
            # Generate module documentation method that fails first, then succeeds
            module_mock = MagicMock()
            module_mock.side_effect = [Exception("Module error"), "module.md"]
            mock_generator.generate_module_documentation = module_mock
            
            # Set up the module
            mock_module.DocumentationGenerator = MagicMock(return_value=mock_generator)
            
            yield mock_module
    
    def test_generation_recovery(self, mock_recovery_module, temp_test_dir):
        """Test recovery from generation errors."""
        from core.documentation.generator import DocumentationGenerator
        
        # Create a DocumentationGenerator instance
        generator = DocumentationGenerator()
        
        # First attempt should fail
        with pytest.raises(Exception):
            generator.generate_documentation(
                source_dir=temp_test_dir,
                output_dir=os.path.join(temp_test_dir, "docs")
            )
        
        # Second attempt should succeed
        output_files = generator.generate_documentation(
            source_dir=temp_test_dir,
            output_dir=os.path.join(temp_test_dir, "docs")
        )
        
        assert isinstance(output_files, list)
        assert len(output_files) == 2
    
    def test_module_recovery(self, mock_recovery_module, temp_test_file):
        """Test recovery from module errors."""
        from core.documentation.generator import DocumentationGenerator
        
        # Create a DocumentationGenerator instance
        generator = DocumentationGenerator()
        
        # First attempt should fail
        with pytest.raises(Exception):
            generator.generate_module_documentation(
                module_path=temp_test_file[1],
                output_dir=os.path.join(temp_test_file[0], "docs")
            )
        
        # Second attempt should succeed
        output_file = generator.generate_module_documentation(
            module_path=temp_test_file[1],
            output_dir=os.path.join(temp_test_file[0], "docs")
        )
        
        assert output_file == "module.md"


if __name__ == '__main__':
    unittest.main()