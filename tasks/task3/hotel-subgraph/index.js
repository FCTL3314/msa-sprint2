import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { buildSubgraphSchema } from '@apollo/subgraph';
import DataLoader from 'dataloader';
import gql from 'graphql-tag';

const MONOLITH_URL = process.env.MONOLITH_URL || 'http://hotelio-monolith:8080';
const CACHE_TTL_MS = 60_000;

const cache = new Map();

async function fetchHotel(id) {
  const cached = cache.get(id);
  if (cached && cached.expiresAt > Date.now()) {
    return cached.hotel;
  }
  const response = await fetch(`${MONOLITH_URL}/api/hotels/${encodeURIComponent(id)}`);
  const hotel = response.status === 404 ? null : toHotel(await response.json());
  cache.set(id, { hotel, expiresAt: Date.now() + CACHE_TTL_MS });
  return hotel;
}

// в монолите у отеля нет name и stars
function toHotel(h) {
  return {
    id: h.id,
    name: h.description,
    city: h.city,
    stars: Math.round(h.rating),
    description: h.description,
  };
}

function createHotelLoader() {
  return new DataLoader(async (ids) => {
    console.log(`hotel batch: ${ids.length} unique ids [${ids.join(', ')}]`);
    return Promise.all(ids.map(fetchHotel));
  });
}

const typeDefs = gql`
  extend schema @link(url: "https://specs.apollo.dev/federation/v2.3", import: ["@key"])

  type Hotel @key(fields: "id") {
    id: ID!
    name: String
    city: String
    stars: Int
    description: String
  }

  type Query {
    hotelsByIds(ids: [ID!]!): [Hotel]!
  }
`;

const resolvers = {
  Hotel: {
    __resolveReference: ({ id }, { hotelLoader }) => hotelLoader.load(id),
  },
  Query: {
    hotelsByIds: (_, { ids }, { hotelLoader }) => hotelLoader.loadMany(ids),
  },
};

const server = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
  includeStacktraceInErrorResponses: false,
});

startStandaloneServer(server, {
  listen: { port: 4002 },
  context: async () => ({ hotelLoader: createHotelLoader() }),
}).then(() => {
  console.log('Hotel subgraph ready at http://localhost:4002/');
});
