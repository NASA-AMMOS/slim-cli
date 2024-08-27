from unittest.mock import mock_open, patch
from jpl.slim.cli import repo_file_to_list

def test_read_git_remotes():
    # mock content of the file
    mock_file_content = "https://github.com/user/repo1.git\nhttps://github.com/user/repo2.git\nhttps://github.com/user/repo3.git"
    
    # use mock_open to simulate file opening and reading
    # it ensures any function called within the block uses mock_file_content not real file data
    with patch('builtins.open', mock_open(read_data=mock_file_content)):
        # call the function with any file path (it's mocked so doesn't matter)
        result = repo_file_to_list("dummy_path")
        
        # expected result
        expected_result = [
            "https://github.com/user/repo1.git",
            "https://github.com/user/repo2.git",
            "https://github.com/user/repo3.git"
        ]
        
        # assert that the function's result matches the expected result
        assert result == expected_result
