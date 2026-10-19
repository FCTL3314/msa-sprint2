import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { buildSubgraphSchema } from '@apollo/subgraph';
import DataLoader from 'dataloader';
import gql from 'graphql-tag';

const MONOLITH_URL = process.env.MONOLITH_URL || 'http://hotelio-monolith:8080';

async function fetchPromo(code) {
  const response = await fetch(`${MONOLITH_URL}/api/promos/${encodeURIComponent(code)}`);
  return response.status === 404 ? null : response.json();
}

function createPromoLoader() {
  return new DataLoader((codes) => Promise.all(codes.map(fetchPromo)));
}

// монолит смотрит только на expired, срок validUntil не проверяет
function toDiscountInfo(promo) {
  if (!promo) {
    return { isValid: false, originalDiscount: 0, finalDiscount: 0, description: null, expiresAt: null, applicableHotels: [] };
  }
  const today = new Date().toISOString().slice(0, 10);
  const isValid = !promo.expired && (!promo.validUntil || promo.validUntil >= today);
  return {
    isValid,
    originalDiscount: promo.discount,
    finalDiscount: isValid ? promo.discount : 0,
    description: promo.description,
    expiresAt: promo.validUntil,
    applicableHotels: [],
  };
}

async function discountInfoFor(promoCode, promoLoader) {
  return toDiscountInfo(promoCode ? await promoLoader.load(promoCode) : null);
}

const typeDefs = gql`
  extend schema @link(
    url: "https://specs.apollo.dev/federation/v2.3"
    import: ["@key", "@external", "@requires", "@override"]
  )

  type Booking @key(fields: "id") {
    id: ID!
    promoCode: String @external
    discountPercent: Float! @override(from: "booking-subgraph") @requires(fields: "promoCode")
    discountInfo: DiscountInfo @requires(fields: "promoCode")
  }

  type DiscountInfo {
    isValid: Boolean!
    originalDiscount: Float!
    finalDiscount: Float!
    description: String
    expiresAt: String
    applicableHotels: [ID!]!
  }

  type Query {
    validatePromoCode(code: String!, hotelId: ID): DiscountInfo!
  }
`;

const resolvers = {
  Booking: {
    discountPercent: async ({ promoCode }, _, { promoLoader }) =>
      (await discountInfoFor(promoCode, promoLoader)).finalDiscount,
    discountInfo: ({ promoCode }, _, { promoLoader }) => (promoCode ? discountInfoFor(promoCode, promoLoader) : null),
  },
  Query: {
    validatePromoCode: (_, { code }, { promoLoader }) => discountInfoFor(code, promoLoader),
  },
};

const server = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
  includeStacktraceInErrorResponses: false,
});

startStandaloneServer(server, {
  listen: { port: 4003 },
  context: async () => ({ promoLoader: createPromoLoader() }),
}).then(() => {
  console.log('Promocode subgraph ready at http://localhost:4003/');
});
