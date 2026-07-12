# Contributing to AI-CTIDS

Thank you for your interest in contributing to the AI-Driven Cyber Threat Detection and Intrusion Detection System!

## Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-ctids.git
   cd ai-ctids
   ```

3. **Set up development environment**
   ```bash
   make setup
   source venv/bin/activate
   make install
   ```

4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Code Style

We follow PEP 8 style guidelines with some modifications:
- Line length: 127 characters
- Use `black` for automatic formatting
- Use `isort` for import sorting

```bash
# Format code
make format

# Check linting
make lint
```

### Type Hints

All new code should include type hints:

```python
def predict(self, X: np.ndarray) -> np.ndarray:
    """Make predictions on input data."""
    return self.model.predict(X)
```

### Documentation

- Use Google-style docstrings
- Document all public functions and classes
- Include examples where appropriate

```python
def calculate_psi(reference: np.ndarray, current: np.ndarray) -> float:
    """Calculate Population Stability Index.
    
    Args:
        reference: Reference distribution from training
        current: Current production distribution
    
    Returns:
        PSI score (0 = no drift, >0.2 = significant drift)
    
    Example:
        >>> ref = np.array([0.5, 0.3, 0.2])
        >>> cur = np.array([0.4, 0.4, 0.2])
        >>> psi = calculate_psi(ref, cur)
        >>> print(f"{psi:.4f}")
    """
```

### Testing

Write tests for all new features:

```bash
# Run tests
make test

# Run specific test
pytest tests/test_predictor.py -v

# Check coverage
pytest tests/ --cov=. --cov-report=html
```

Example test:

```python
import pytest
from shared.schemas import NetworkFlowEvent

def test_network_flow_event_validation():
    """Test NetworkFlowEvent validates correctly."""
    event = NetworkFlowEvent(
        destination_port=80,
        flow_duration=1234.5,
        # ... other required fields
    )
    
    assert event.destination_port == 80
    assert 0 <= event.destination_port <= 65535
```

## Pull Request Process

1. **Update documentation**
   - Update README.md if needed
   - Add docstrings to new functions
   - Update API.md for endpoint changes

2. **Run tests**
   ```bash
   make test
   make lint
   ```

3. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add feature X"
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
   - Provide clear description
   - Reference related issues
   - Add screenshots if UI changes

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `test:` Test additions or changes
- `chore:` Build/tooling changes

Examples:
```
feat: add batch prediction endpoint
fix: correct PSI calculation for edge cases
docs: update deployment guide with K8s instructions
```

## Code Review

All submissions require review:
- At least one approval required
- All tests must pass
- No merge conflicts
- Documentation updated

## Project Structure

Please follow the existing structure:

```
ai-ctids/
├── shared/              # Shared utilities
├── batch-trainer/       # Training pipeline
├── inference-api/       # REST API
├── streaming-consumer/  # Kafka consumer
├── data-ingestion/      # Data ingestion
├── drift-monitor/       # Drift detection
├── observability/       # Monitoring configs
└── docs/               # Documentation
```

## Adding New Models

1. Implement in `batch-trainer/train.py`
2. Add evaluation in `batch-trainer/evaluate.py`
3. Update `inference-api/predictor.py` for loading
4. Add to CI/CD pipeline
5. Document in README.md

## Questions?

- Open an issue for bugs
- Use Discussions for questions
- Check existing issues first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
