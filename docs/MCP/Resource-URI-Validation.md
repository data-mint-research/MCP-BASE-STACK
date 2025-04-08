# Resource URI Validation in MCP

This document describes the resource URI validation implementation in the MCP-BASE-STACK project.

## Overview

Resource URIs in the Model Context Protocol (MCP) must follow a specific format to ensure consistency and proper routing of resource requests. The format is:

```
resource://provider/path
```

Where:
- `resource://` is the scheme (required)
- `provider` is the resource provider (required)
- `path` is the path to the resource (optional)

## Implementation

Resource URI validation is implemented in two key components:

1. **Client Component (`MCPClient`)**: Validates resource URIs before sending requests to the server
2. **Resource Subscriber (`ResourceSubscriberManager`)**: Validates resource URIs before subscribing to resources

Both implementations use the same validation logic:

1. First, try to use the SDK's `JsonRpc.validate_resource_uri` method if available
2. If not available, fall back to custom validation:
   - Check that the URI is a string
   - Check that the URI starts with `resource://`
   - Check that the URI has a provider component

## Validation Logic

The validation logic is implemented using a regular expression pattern:

```python
resource_uri_pattern = re.compile(r'^resource://([^/]+)(/.*)?$')
```

This pattern ensures:
- The URI starts with `resource://`
- There is a provider component (`[^/]+`)
- The path component is optional (`(/.*)?`)

## Error Handling

When an invalid resource URI is detected, a `ValidationError` is raised with a descriptive error message:

```python
raise ValidationError(
    message=f"Invalid resource URI format: {uri}. Must follow 'resource://provider/path' format.",
    field_errors={"uri": [f"Invalid resource URI format: {uri}. Must follow 'resource://provider/path' format."]}
)
```

## Integration Points

Resource URI validation is integrated at the following points:

1. **Client's `access_resource` method**: Validates the URI before sending a request to the server
2. **Client's `subscribe_to_resource` method**: Validates the URI before subscribing to a resource
3. **ResourceSubscriberManager's `subscribe` method**: Validates the URI before creating a subscription

## Testing

Unit tests for resource URI validation are provided in `tests/unit/test_resource_uri_validation.py`. These tests verify:

1. Valid resource URIs are accepted
2. Invalid resource URIs are rejected
3. The `access_resource` method validates URIs before sending requests
4. The `subscribe_to_resource` method validates URIs before creating subscriptions

## Examples

### Valid Resource URIs

```
resource://file/path/to/file.txt
resource://system/info
resource://config/settings.json
resource://user/profile
resource://security/keys/public
```

### Invalid Resource URIs

```
file://path/to/file.txt  (wrong scheme)
http://example.com       (wrong scheme)
resource:/               (missing provider)
resource://              (missing provider)
resource:///path/to/file.txt  (missing provider)
```

## Benefits

Implementing resource URI validation provides several benefits:

1. **Early Error Detection**: Invalid URIs are detected before sending requests to the server
2. **Reduced Network Traffic**: Invalid requests are not sent over the network
3. **Improved User Experience**: Clear error messages help developers identify and fix issues
4. **Protocol Compliance**: Ensures all resource URIs follow the MCP specification