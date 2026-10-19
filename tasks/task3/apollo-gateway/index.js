import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { ApolloGateway, IntrospectAndCompose, RemoteGraphQLDataSource } from '@apollo/gateway';

// на имя booking-subgraph ссылается @override в promocode-subgraph
const gateway = new ApolloGateway({
  supergraphSdl: new IntrospectAndCompose({
    subgraphs: [
      { name: 'booking-subgraph', url: 'http://booking-subgraph:4001' },
      { name: 'hotel-subgraph', url: 'http://hotel-subgraph:4002' },
      { name: 'promocode-subgraph', url: 'http://promocode-subgraph:4003' },
    ],
  }),
  // сам шлюз заголовки клиента в подграфы не передаёт
  buildService: ({ url }) => new RemoteGraphQLDataSource({
    url,
    willSendRequest({ request, context }) {
      const userId = context.req?.headers?.userid;
      if (userId) {
        request.http.headers.set('userid', userId);
      }
    },
  }),
});

const server = new ApolloServer({ gateway, includeStacktraceInErrorResponses: false });

startStandaloneServer(server, {
  listen: { port: 4000 },
  context: async ({ req }) => ({ req }),
}).then(({ url }) => {
  console.log(`Gateway ready at ${url}`);
});
