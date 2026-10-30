# uri-cardinality-reducer
The purpose of this module is to provide a callable function that takes a typical URI with parameters and high-cardinality data and returns a transformed URI resembling a the URI template with all high-cardinality data removed.  Reducing the cardinality of the real URI to basic URI template with placeholders allows that data to be used in clustering exercises, GROUP BY expressions, and similar analytical purposes that rely on groupings.

### Installation
pip install uri_cardinality_reducer

### Example usage:
`from uri_cardinality_reducer import UriCardinalityReducer
reducer = UriCardinalityReducer(include_query=True)

high_cardinality_uri = "https://example.com/users/550e8400-e29b-41d4-a716-446655440000/profile"
reduced_cardinality_uri = reducer.extract(high_cardinality_uri)
print(reduced_cardinality_uri)`

The output should be:
`https://example.com/users/<UUID>/profile`

### Additional examples:
  | Original URI | URI masked template |
  | :--- | :--- |
  | `https://example.com/users/bobjones/posts/789` | `https://example.com/users/<USER>/posts/<NUM>` |
  | `https://api.example.com/v1/orders/2024-01-15/items/42` | `https://api.example.com/v<<NUM>>/orders/<USER>/items/<NUM>` |
  | `https://example.com/users/550e8400-e29b-41d4-a716-446655440000/profile` | `https://example.com/users/<UUID>/profile` |
  
