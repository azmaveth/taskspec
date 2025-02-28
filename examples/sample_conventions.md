# TaskSpec Coding Conventions and Design Preferences

## General Architecture Principles
- Prefer loose coupling between components
- Follow SOLID principles for all class designs
- Use event-driven architecture for scalable systems
- Implement domain-driven design for complex domains
- Employ defensive programming techniques

## Language-Specific Preferences
- Python: Use type hints for all function parameters and returns
- JavaScript: Use TypeScript for all new frontend components
- Go: Follow the standard style guide with 'gofmt'
- Rust: Prefer Result types over panics for error handling

## Security Practices
- Implement proper input validation at all entry points
- Use parameterized queries for database operations
- Apply minimum necessary permissions (principle of least privilege)
- Store credentials in environment variables, never in code

## Database Design
- Use ORM for database interactions when possible
- Implement migrations for all schema changes
- Keep indexes on frequently queried columns
- Use UUIDs instead of sequential IDs for public-facing resources

## API Design
- Design REST APIs following standard conventions
- Implement authentication with OAuth2/JWT where appropriate
- Version all APIs using URL prefixes
- Apply proper response codes and error messages

## Testing Standards
- Write unit tests for all non-trivial functions
- Maintain at least 80% test coverage for core modules
- Implement integration tests for critical paths
- Use property-based testing for data-intensive components

## Infrastructure Preferences
- Use containerization with Docker for all services
- Implement CI/CD pipelines for all repositories
- Store configuration in environment variables or config files
- Apply infrastructure as code principles