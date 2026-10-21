const tiersService = require('../../services/tiers');
const labs = require('../../../shared/labs');
const { COLLECTION_FLAG } = require('../../services/stripe-checkout-config/models');

// What a tier's members must give is listed only while collecting it at checkout is in Labs.
const withRequirements = () => labs.isSet(COLLECTION_FLAG);

/** @type {import('@tryghost/api-framework').Controller} */
const controller = {
  docName: 'tiers',

  browse: {
    headers: {
      cacheInvalidate: false,
    },
    options: ['limit', 'fields', 'filter', 'order', 'debug', 'page'],
    permissions: {
      docName: 'products',
    },
    async query(frame) {
      const page = await tiersService.api.browse({
        ...frame.options,
        withRequirements: withRequirements(),
      });
      return page;
    },
  },

  read: {
    headers: {
      cacheInvalidate: false,
    },
    data: ['id'],
    permissions: {
      docName: 'products',
    },
    async query(frame) {
      return await tiersService.api.read(frame.data.id, { withRequirements: withRequirements() });
    },
  },

  add: {
    statusCode: 201,
    headers: {
      cacheInvalidate: true,
    },
    validation: {
      data: {
        name: { required: true },
      },
    },
    permissions: {
      docName: 'products',
    },
    async query(frame) {
      const tier = await tiersService.api.add(frame.data);
      // Read back for what its members must give, as a requirement on every paid tier covers it.
      return await tiersService.api.read(tier.id.toHexString(), {
        withRequirements: withRequirements(),
      });
    },
  },

  edit: {
    statusCode: 200,
    options: ['id'],
    headers: {
      cacheInvalidate: true,
    },
    validation: {
      options: {
        id: {
          required: true,
        },
      },
    },
    permissions: {
      docName: 'products',
    },
    async query(frame) {
      await tiersService.api.edit(frame.options.id, frame.data);
      return await tiersService.api.read(frame.options.id, {
        withRequirements: withRequirements(),
      });
    },
  },
};

module.exports = controller;
