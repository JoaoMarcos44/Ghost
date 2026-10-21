const { BadRequestError } = require('@tryghost/errors');
const Tier = require('./tier');
const nql = require('@tryghost/nql');
const { products } = require('../../data/schema/schema');

/** The fields a tier can be filtered by: the columns of `products`. */
const FILTERABLE = new Set(Object.keys(products));

/**
 * The fields a mongo query object filters on, looking inside `$and`, `$or` and the like.
 * @param {unknown} filter
 * @returns {string[]}
 */
function filteredFields(filter) {
  if (Array.isArray(filter)) {
    return filter.flatMap(filteredFields);
  }
  if (!filter || typeof filter !== 'object') {
    return [];
  }
  return Object.entries(filter).flatMap(([key, value]) =>
    key.startsWith('$') ? filteredFields(value) : [key],
  );
}

/**
 * @typedef {import('./tiers-api').ITierRepository} ITierRepository
 */

/**
 * Reads and saves tiers in the database on every call, keeping nothing between calls, so every
 * Ghost instance serving a site sees the same tiers.
 *
 * @implements {ITierRepository}
 */
module.exports = class TierRepository {
  /** @type {Object} */
  #ProductModel;

  /** @type {import('@tryghost/domain-events')} */
  #DomainEvents;

  /** @type {import('./requirements').TierRequirements} */
  #requirements;

  /**
   * @param {object} deps
   * @param {object} deps.ProductModel Bookshelf Model
   * @param {import('@tryghost/domain-events')} deps.DomainEvents
   * @param {import('./requirements').TierRequirements} deps.requirements
   */
  constructor(deps) {
    this.#ProductModel = deps.ProductModel;
    this.#DomainEvents = deps.DomainEvents;
    this.#requirements = deps.requirements;
  }

  /**
   * The tiers these rows hold, with what each one's members must give when asked for.
   *
   * @param {Array<object>} models
   * @param {object} options
   * @param {boolean} [options.withRequirements]
   * @param {import('knex').Knex.Transaction} [options.transacting]
   * @returns {Promise<import('./tier')[]>}
   */
  async #toTiers(models, options) {
    const data = models.map((model) => this.mapToTier(model));
    const requirements = options.withRequirements
      ? await this.#requirements.forTiers(data, { transacting: options.transacting })
      : null;
    return Promise.all(
      data.map((tier) =>
        Tier.create(requirements ? { ...tier, requirements: requirements.get(tier.id) } : tier),
      ),
    );
  }

  /**
   * @private
   */
  mapToTier(model) {
    const json = model.toJSON();
    return {
      id: json.id,
      name: json.name,
      slug: json.slug,
      status: json.active ? 'active' : 'archived',
      welcomePageURL: json.welcome_page_url,
      visibility: json.visibility,
      trialDays: json.trial_days,
      description: json.description,
      type: json.type,
      currency: json.currency,
      monthlyPrice: json.monthly_price,
      yearlyPrice: json.yearly_price,
      createdAt: json.created_at,
      updatedAt: json.updated_at,
      benefits: json.benefits.map((item) => item.name),
    };
  }

  /**
   * Every tier the filter matches, cheapest first.
   *
   * @param {object} [options]
   * @param {object} [options.filter] - A mongo query object over the tier's columns
   * @param {boolean} [options.withRequirements] - Reads what each tier's members must give
   * @param {import('knex').Knex.Transaction} [options.transacting] - Reads inside it
   * @returns {Promise<import('./tier')[]>}
   */
  async getAll(options = {}) {
    const unknown = filteredFields(options.filter).find((field) => !FILTERABLE.has(field));
    if (unknown) {
      throw new BadRequestError({ message: `Tiers can't be filtered by ${unknown}.` });
    }
    const models = await this.#ProductModel
      .forge()
      .query((qb) => {
        if (options.filter) {
          const query = nql();
          query.filter = options.filter;
          query.querySQL(qb);
        }
        qb.orderByRaw(this.#ProductModel.orderDefaultRaw());
      })
      .fetchAll({ withRelated: ['benefits'], transacting: options.transacting });
    return this.#toTiers(models.models, options);
  }

  /**
   * @param {import('bson-objectid').default} id
   * @param {object} [options]
   * @param {boolean} [options.withRequirements] - Reads what the tier's members must give
   * @param {import('knex').Knex.Transaction} [options.transacting] - Reads inside it
   * @returns {Promise<import('./tier')>}
   */
  async getById(id, options = {}) {
    const model = await this.#ProductModel.findOne(
      { id: id.toHexString() },
      { withRelated: ['benefits'], transacting: options.transacting },
    );
    if (!model) {
      return null;
    }
    const [tier] = await this.#toTiers([model], options);
    return tier;
  }

  /**
   * @param {import('./tier')} tier
   * @returns {Promise<void>}
   */
  async save(tier) {
    const data = {
      id: tier.id.toHexString(),
      name: tier.name,
      slug: tier.slug,
      active: tier.status === 'active',
      welcome_page_url: tier.welcomePageURL,
      visibility: tier.visibility,
      trial_days: tier.trialDays,
      description: tier.description,
      type: tier.type,
      currency: tier.currency,
      monthly_price: tier.monthlyPrice,
      yearly_price: tier.yearlyPrice,
      created_at: tier.createdAt,
      updated_at: tier.updatedAt,
      benefits: tier.benefits.map((name) => ({ name })),
    };

    const existing = await this.#ProductModel.findOne({ id: data.id });
    if (existing) {
      await this.#ProductModel.edit(data, {
        id: data.id,
      });
    } else {
      await this.#ProductModel.add(data);
    }

    for (const event of tier.events) {
      this.#DomainEvents.dispatch(event);
    }
  }
};
