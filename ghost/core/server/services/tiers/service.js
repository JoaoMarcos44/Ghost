const { IncorrectUsageError } = require('@tryghost/errors');

class TiersServiceWrapper {
  async init() {
    if (this.api) {
      // Already done
      return;
    }

    const TiersAPI = require('./tiers-api');
    const DomainEvents = require('@tryghost/domain-events');

    const models = require('../../models');
    const { knex } = require('../../data/db');
    const metafields = require('../members-metafields');
    const TierRepository = require('./tier-repository');
    const { TierRequirements } = require('./requirements');

    const requirements = new TierRequirements({
      knex,
      fieldsFor: (db, ports) => {
        if (!metafields.bindings) {
          throw new IncorrectUsageError({
            message: 'The custom fields services must be set up before tier requirements are read.',
          });
        }
        return metafields.bindings.fieldsFor(db, ports);
      },
    });

    const repository = new TierRepository({
      ProductModel: models.Product,
      DomainEvents,
      requirements,
    });

    const slugService = {
      async generate(input) {
        return models.Product.generateSlug(models.Product, input, {});
      },
    };

    this.requirements = requirements;
    this.api = new TiersAPI({
      repository,
      slugService,
    });
  }
}

module.exports = new TiersServiceWrapper();
