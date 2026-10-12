import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { buildSubgraphSchema } from '@apollo/subgraph';
import { GraphQLError } from 'graphql';
import gql from 'graphql-tag';
import grpc from '@grpc/grpc-js';
import protoLoader from '@grpc/proto-loader';

const BOOKING_SERVICE_ADDR = process.env.BOOKING_SERVICE_ADDR || 'booking-service:9090';

const proto = grpc.loadPackageDefinition(
  protoLoader.loadSync('booking.proto', { keepCase: true, defaults: true }),
);
const bookingClient = new proto.booking.BookingService(BOOKING_SERVICE_ADDR, grpc.credentials.createInsecure());

function listBookings(userId) {
  return new Promise((resolve, reject) => {
    bookingClient.ListBookings({ user_id: userId }, (error, response) => {
      if (error) reject(error);
      else resolve(response.bookings);
    });
  });
}

const typeDefs = gql`
  extend schema @link(url: "https://specs.apollo.dev/federation/v2.3", import: ["@key"])

  type Booking @key(fields: "id") {
    id: ID!
    userId: String!
    hotelId: String!
    promoCode: String
    discountPercent: Float
    hotel: Hotel
  }

  type Hotel @key(fields: "id", resolvable: false) {
    id: ID!
  }

  type Query {
    bookingsByUser(userId: String!): [Booking]
  }
`;

const resolvers = {
  Query: {
    bookingsByUser: async (_, { userId }, { req }) => {
      const caller = req.headers['userid'];
      if (!caller || caller !== userId) {
        console.log(`DENY bookingsByUser(userId=${userId}) caller=${caller || '-'}`);
        throw new GraphQLError('Access denied: you can see only your own bookings', {
          extensions: { code: 'FORBIDDEN' },
        });
      }
      const bookings = await listBookings(userId);
      console.log(`ALLOW bookingsByUser(userId=${userId}) caller=${caller}: ${bookings.length} bookings via gRPC`);
      return bookings.map((b) => ({
        id: b.id,
        userId: b.user_id,
        hotelId: b.hotel_id,
        promoCode: b.promo_code || null,
        discountPercent: b.discount_percent,
      }));
    },
  },
  Booking: {
    hotel: (booking) => ({ __typename: 'Hotel', id: booking.hotelId }),
  },
};

const server = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
  includeStacktraceInErrorResponses: false,
});

startStandaloneServer(server, {
  listen: { port: 4001 },
  context: async ({ req }) => ({ req }),
}).then(() => {
  console.log('Booking subgraph ready at http://localhost:4001/');
});
