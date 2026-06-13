# Load a suitable python module
module load python/3.11.9

# Create a local virtual environment for the current Python version
python3.11 -m venv py311

# Activate the virtual environment
source py311/bin/activate

# Install uv inside the environment - use to install other packages faster!
python -m pip install uv

# Test installation
uv --version

# Download test model from huggingface and store locally
uvx hf download Qwen/Qwen3-4B-Instruct-2507 --local-dir Qwen3-4B-Instruct-2507
uvx hf download Qwen/Qwen3-4B-Thinking-2507 --local-dir Qwen3-4B-Thinking-2507

# Install needed packages
uv pip install -r requirements.txt
# Load a suitable python module
module load python/3.11.9

# Create a local virtual environment for the current Python version
python3.11 -m venv py311

# Activate the virtual environment
source py311/bin/activate

# Install uv inside the environment - use to install other packages faster!
python -m pip install uv

# Test installation
uv --version

# Download test model from huggingface and store locally
uvx hf download Qwen/Qwen3-4B-Instruct-2507 --local-dir Qwen3-4B-Instruct-2507
uvx hf download Qwen/Qwen3-4B-Thinking-2507 --local-dir Qwen3-4B-Thinking-2507

# Install needed packages
uv pip install -r requirements.txt

