# GraphQL API Structure

Your `graphql/` directory is structured in a way that follows a modular approach for defining and managing GraphQL queries, mutations, and types. Here’s a breakdown of its components and how they fit together:


## 📁 Directory Structure
```
graphql/
│── __init__.py       # Marks this directory as a package
│── inputs.py         # Defines input types for mutations/queries
│── resolvers.py      # Contains resolver functions for queries and mutations
│── schema.py         # Defines the GraphQL schema, including queries and mutations
│── types.py          # Defines output types (GraphQL object types)
└── __pycache__/      # Compiled Python files (can be ignored)
```

### **File Responsibilities**
1. **`inputs.py`**  
   - Defines **input types** (e.g., for mutations) using `@strawberry.input`.
   - Example: If you need a mutation that requires user input, you’d define a corresponding input type here.

2. **`resolvers.py`**  
   - Houses **resolver functions** that process queries and mutations.
   - Each function fetches or modifies data, handling the logic for interacting with models or storage.
   - Example: A query resolver might fetch a specific GeoJSON from the database or file system.

3. **`schema.py`**  
   - Assembles the GraphQL schema.
   - Imports types from `types.py`, queries/mutations from `resolvers.py`, and inputs from `inputs.py`.
   - Registers all components with Strawberry.

4. **`types.py`**  
   - Defines **GraphQL object types** (i.e., responses).
   - Example: If a query returns a GeoJSON, this file defines the GraphQL representation of that GeoJSON.

5. **`__init__.py`**  
   - Helps Python recognize `graphql/` as a module.
   - Sometimes used for global imports or initialization logic.

### **Where to Place Additional Logic?**
If a request requires additional logic (e.g., fetching data, processing an image, validating input), here’s where to put it:

- **Data fetching or processing logic?** → Place in `resolvers.py`
- **Shared helper functions?** → Create a new `utils.py` in `graphql/` or use an appropriate module.
- **Complex business logic?** → Consider placing it in a separate service layer (e.g., `services/geojson_service.py`).
- **Database interactions?** → Could go in a `models/` directory or a dedicated repository pattern (if using a database).
- **Queries & Mutations:** Defined in `resolvers.py` and registered in `schema.py`.
- **Input Types:** Defined in `inputs.py` for handling structured input in mutations.
- **Output Types:** Defined in `types.py` for structuring API responses.

## ✅ Adding a New Query

1. **Define an Output Type**  
   Add a new type in `types.py`:
   ```python
   import strawberry

   @strawberry.type
   class GeoJSON:
       type: str
       coordinates: list
   ```

2. **Write a Resolver Function**  
   Add the logic in `resolvers.py`:
   ```python
   from .types import GeoJSON

   def get_geojson() -> GeoJSON:
       return GeoJSON(type="Point", coordinates=[-122.4194, 37.7749])
   ```

3. **Register the Query**  
   Add it to `schema.py`:
   ```python
   import strawberry
   from .resolvers import get_geojson

   @strawberry.type
   class Query:
       geojson: GeoJSON = strawberry.field(resolver=get_geojson)

   schema = strawberry.Schema(query=Query)
   ```

4. **Test the Query**  
   Run your GraphQL server and query:
   ```graphql
   {
       geojson {
           type
           coordinates
       }
   }
   ```

## ✅ Adding a New Mutation

1. **Define an Input Type**  
   In `inputs.py`:
   ```python
   import strawberry

   @strawberry.input
   class CreateGeoJSONInput:
       type: str
       coordinates: list
   ```

2. **Write the Resolver Function**  
   In `resolvers.py`:
   ```python
   from .inputs import CreateGeoJSONInput
   from .types import GeoJSON

   def create_geojson(input: CreateGeoJSONInput) -> GeoJSON:
       return GeoJSON(type=input.type, coordinates=input.coordinates)
   ```

3. **Register the Mutation**  
   In `schema.py`:
   ```python
   @strawberry.type
   class Mutation:
       create_geojson: GeoJSON = strawberry.mutation(resolver=create_geojson)

   schema = strawberry.Schema(query=Query, mutation=Mutation)
   ```

4. **Test the Mutation**  
   ```graphql
   mutation {
       createGeojson(input: { type: "Polygon", coordinates: [[0,0],[1,1],[1,0],[0,0]] }) {
           type
           coordinates
       }
   }
   ```

## 📌 Notes
- Place additional logic in `resolvers.py` or `utils.py` for reusability.
- Use `inputs.py` for structured inputs.
- Always update `schema.py` to register new queries and mutations.

