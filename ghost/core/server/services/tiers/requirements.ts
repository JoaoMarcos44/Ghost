import type { Knex } from 'knex';
import { z } from 'zod';
import { PORT_PARTS, isAskable, isRequiredPort, type RequiredPort } from '@tryghost/checkout';
import type { PortField } from '../members-metafields';

const REQUIREMENTS_TABLE = 'tier_requirements';
const REQUIREMENT_TIERS_TABLE = 'tier_requirement_tiers';

/** The paid tiers a requirement covers: null for every paid tier, including tiers added later. */
export type RequiredTiers = string[] | null;

/** What a tier's members must give: what a port collects, and the custom fields it's kept in. */
export interface TierRequirement {
  /** The port a checkout collects it under, such as `checkout.shipping`. */
  port: RequiredPort;
  /** The fields it's kept in: one for each of its parts whose field can take a value. */
  customFields: PortField[];
}

/**
 * One row of the requirements read: a requirement, and one tier it names again only if that tier
 * is paid (or null). A requirement naming several tiers comes back as a row for each.
 */
const ReadRow = z.object({
  port: z.string(),
  tier_scope: z.enum(['all_paid', 'selected_paid']),
  paid_tier_id: z.string().nullable(),
});

interface ReadOptions {
  transacting?: Knex.Transaction;
}

/**
 * What each tier's members must give, named by the port a checkout collects it under: on every
 * paid tier, including tiers added later, or only on the paid tiers named for it. Whatever
 * collects a port asks for it on those tiers, and the custom field each part of it is kept in is
 * the port's binding.
 */
export class TierRequirements {
  private knex: Knex;
  private fieldsFor: (db: Knex, ports: readonly string[]) => Promise<Map<string, PortField>>;

  constructor({
    knex,
    fieldsFor,
  }: {
    knex: Knex;
    fieldsFor: (db: Knex, ports: readonly string[]) => Promise<Map<string, PortField>>;
  }) {
    this.knex = knex;
    this.fieldsFor = fieldsFor;
  }

  /**
   * The paid tiers each of these ports is required on, leaving out ports nothing requires. A
   * requirement only counts the named tiers that are paid, and once every tier it named has been
   * deleted it requires nothing, rather than widening to every paid tier.
   */
  async read(
    ports: readonly RequiredPort[],
    { transacting }: ReadOptions = {},
  ): Promise<Map<RequiredPort, RequiredTiers>> {
    return this.readWhere(transacting ?? this.knex, ports);
  }

  /**
   * What each of these tiers' members must give, by tier, as checkouts would ask for it: a port
   * is left out while it can't be asked for, and a part whose field is archived is left out.
   */
  async forTiers(
    tiers: ReadonlyArray<{ id: string; type: string }>,
    { transacting }: ReadOptions = {},
  ): Promise<Map<string, TierRequirement[]>> {
    const db = transacting ?? this.knex;
    const required = await this.readWhere(db, null);
    const fields = await this.fieldsFor(
      db,
      [...required.keys()].flatMap((port) => PORT_PARTS[port].map((part) => part.port)),
    );
    const ready = (part: string) => {
      const field = fields.get(part);
      return field && { field, ready: field.status === 'active' };
    };
    const askable = [...required].flatMap(([port, tierIds]) => {
      if (!isAskable(port, ready)) {
        return [];
      }
      const customFields = PORT_PARTS[port].flatMap(({ port: part }) => {
        const kept = ready(part);
        return kept?.ready ? [kept.field] : [];
      });
      return [{ port, tierIds, customFields }];
    });

    return new Map(
      tiers.map((tier): [string, TierRequirement[]] => [
        tier.id,
        tier.type === 'paid'
          ? askable
              .filter(({ tierIds }) => tierIds === null || tierIds.includes(tier.id))
              .map(({ port, customFields }) => ({ port, customFields }))
          : [],
      ]),
    );
  }

  /**
   * Requires the port of members on these paid tiers, or on every paid tier for null, in place
   * of whatever it required before.
   */
  async require(
    port: RequiredPort,
    tierIds: RequiredTiers,
    now: Date,
    { transacting }: { transacting: Knex.Transaction },
  ): Promise<void> {
    const tierScope = tierIds ? 'selected_paid' : 'all_paid';
    await transacting(REQUIREMENTS_TABLE)
      .insert({ port, tier_scope: tierScope, created_at: now, updated_at: now })
      .onConflict('port')
      .merge({ tier_scope: tierScope, updated_at: now });

    await transacting(REQUIREMENT_TIERS_TABLE).where('port', port).del();
    if (tierIds?.length) {
      await transacting(REQUIREMENT_TIERS_TABLE).insert(
        tierIds.map((productId) => ({ port, product_id: productId })),
      );
    }
  }

  /** Stops requiring the port on any tier. */
  async release(
    port: RequiredPort,
    { transacting }: { transacting: Knex.Transaction },
  ): Promise<void> {
    await transacting(REQUIREMENT_TIERS_TABLE).where('port', port).del();
    await transacting(REQUIREMENTS_TABLE).where('port', port).del();
  }

  /** The requirements for these ports, or for every port when null. */
  private async readWhere(
    db: Knex,
    ports: readonly RequiredPort[] | null,
  ): Promise<Map<RequiredPort, RequiredTiers>> {
    if (ports?.length === 0) {
      return new Map();
    }
    const query = db(`${REQUIREMENTS_TABLE} as requirement`)
      .leftJoin(`${REQUIREMENT_TIERS_TABLE} as named`, 'named.port', 'requirement.port')
      .leftJoin('products as tier', (join) =>
        join.on('tier.id', '=', 'named.product_id').andOnVal('tier.type', '=', 'paid'),
      )
      .orderBy('requirement.port')
      .select('requirement.port', 'requirement.tier_scope', 'tier.id as paid_tier_id');
    const rows = z
      .array(ReadRow)
      .parse(ports ? await query.whereIn('requirement.port', ports) : await query);

    const required = new Map<RequiredPort, RequiredTiers>();
    for (const { port, tier_scope: tierScope, paid_tier_id: tierId } of rows) {
      // A port no longer offered requires nothing.
      if (!isRequiredPort(port)) {
        continue;
      }
      if (tierScope === 'all_paid') {
        required.set(port, null);
      } else if (tierId) {
        required.set(port, [...new Set([...(required.get(port) ?? []), tierId])]);
      }
    }
    return required;
  }
}

declare module 'knex/types/tables' {
  interface Tables {
    tier_requirements: Knex.CompositeTableType<{
      port: string;
      tier_scope: 'all_paid' | 'selected_paid';
      created_at: Date;
      updated_at: Date | null;
    }>;
    tier_requirement_tiers: Knex.CompositeTableType<{ port: string; product_id: string }>;
  }
}
