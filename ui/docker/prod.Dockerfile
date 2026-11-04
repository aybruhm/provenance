# Build stage
FROM node:25-slim AS build

WORKDIR /app

COPY package*.json .npmrc ./
RUN npm ci

COPY . .
RUN npm run build
RUN npm prune --omit=dev


# Runtime stage - hardened image
FROM dhi.io/node:25-debian13-sfw-dev

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000

USER 65532:65532

COPY --chown=65532:65532 --from=build /app/build ./build
COPY --chown=65532:65532 --from=build /app/package*.json ./
COPY --chown=65532:65532 --from=build /app/node_modules ./node_modules

LABEL org.opencontainers.image.source=https://github.com/aybruhm/provenance
LABEL org.opencontainers.image.description="Provenance UI — web console for governing AI agents: manage policies, review and approve escalations, explore audit trails, and export SOC 2, GDPR, and PCI-DSS compliance reports"
LABEL org.opencontainers.image.licenses=GPL-2.0

EXPOSE 3000

CMD ["node", "build/index.js"]
