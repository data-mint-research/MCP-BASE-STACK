# Dependency Injection Framework

This directory contains the dependency injection (DI) framework for the MCP Server. The framework is built using the `dependency-injector` library and provides a clean, modular way to manage dependencies throughout the application.

## Overview

Dependency injection is a design pattern that allows us to:

1. Decouple components from their dependencies
2. Make components more testable by allowing dependencies to be mocked
3. Centralize configuration and dependency management
4. Improve code maintainability and readability

## Structure

The DI framework consists of the following components:

- **Container**: The central registry that manages all dependencies
- **Providers**: Classes that create and configure services
- **Services**: The actual business logic components that use injected dependencies

## Files

- `__init__.py`: Exports the main components of the DI framework
- `containers.py`: Defines the DI container and wires up dependencies
- `providers.py`: Contains provider classes for creating services

## How to Use

### 1. Injecting Dependencies in Services

Services should accept their dependencies through their constructor:

```python
class MyService:
    def __init__(self, logger: logging.Logger, config: Dict[str, Any]):
        self.logger = logger
        self.config = config
        
    def do_something(self):
        self.logger.info("Doing something with config: %s", self.config)
        # ...
```

### 2. Registering Services in the Container

Add your service to the container in `containers.py`:

```python
class Container(containers.DeclarativeContainer):
    # ...
    
    my_service = providers.Singleton(
        MyService,
        logger=logger,
        config=config
    )
```

### 3. Using Services in FastAPI Endpoints

Create a dependency function and use FastAPI's dependency injection:

```python
# Dependency to get the service
def get_my_service() -> MyService:
    return container.my_service()

@app.get("/my-endpoint")
def my_endpoint(my_service: MyService = Depends(get_my_service)):
    return my_service.do_something()
```

## Example

See the `ExampleService` in `services/example_service.py` for a complete example of how to create a service that uses dependency injection. The service is registered in the container and used in the `/example/info` and `/example/process` endpoints.

## Testing with Dependency Injection

One of the main benefits of dependency injection is improved testability. Here's how you can test components that use DI:

```python
def test_example_service():
    # Create mock dependencies
    mock_logger = MagicMock(spec=logging.Logger)
    mock_config = {"server": {"host": "localhost", "port": 8000}}
    
    # Create the service with mock dependencies
    service = ExampleService(logger=mock_logger, config=mock_config)
    
    # Test the service
    result = service.get_service_info()
    
    # Assert expectations
    assert result["name"] == "ExampleService"
    assert result["server_config"] == {"host": "localhost", "port": 8000}
    mock_logger.info.assert_called_once()
```

## Best Practices

1. **Constructor Injection**: Always inject dependencies through the constructor
2. **Interface Segregation**: Inject only what is needed
3. **Singleton vs Factory**: Use Singleton for stateful services, Factory for stateless ones
4. **Configuration**: Keep configuration separate from business logic
5. **Documentation**: Document what each service does and its dependencies