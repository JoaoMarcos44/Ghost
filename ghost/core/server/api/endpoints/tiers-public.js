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
    permissions: true,
    async query(frame) {
      const page = await tiersService.api.browse({
        ...frame.options,
        withRequirements: withRequirements(),
      });

      return page;
    },
  },
};

module.exports = controller;
