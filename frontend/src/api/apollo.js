import { ApolloClient, InMemoryCache, createHttpLink } from "@apollo/client/core";

const apiBaseURL = import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? "http://localhost:8000/graphql" : "/graphql");

const httpLink = createHttpLink({
  uri: apiBaseURL,  // Backend GraphQL endpoint
});

const apolloClient = new ApolloClient({
  link: httpLink,
  cache: new InMemoryCache(),
});

export default apolloClient;
