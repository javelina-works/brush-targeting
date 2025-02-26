import {
  ApolloClient,
  InMemoryCache,
  createHttpLink,
} from "@apollo/client/core";

const apiBaseURL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/graphql";

// Unsure about this line. When would we want just /graphql?
// (import.meta.env.DEV ? "http://localhost:8000/graphql" : "/graphql");

const httpLink = createHttpLink({
  uri: apiBaseURL, // Backend GraphQL endpoint
});

const apolloClient = new ApolloClient({
  link: httpLink,
  cache: new InMemoryCache(),
});

export default apolloClient;
