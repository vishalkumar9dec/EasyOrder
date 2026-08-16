import { SpendView } from '../accountModel';

/**
 * Total committed spend through EasyOrder, shown above both order listings.
 *
 * The headline is lifetime spend, not the sum of what's on screen — the
 * listings are paginated, the total is not.
 */
export function SpendSummary({ spend }: { spend: SpendView }) {
  if (spend.isEmpty) return null;

  return (
    <div className="spend-summary" aria-label="Total spend">
      <div className="spend-total">
        <p className="spend-label">Total spent</p>
        <p className="spend-amount">{spend.totalLabel}</p>
        <p className="spend-caption">{spend.ordersLabel}</p>
      </div>
      <dl className="spend-breakdown">
        <div>
          <dt>Group orders</dt>
          <dd>{spend.groupOrdersLabel}</dd>
        </div>
        <div>
          <dt>Restaurant orders</dt>
          <dd>{spend.restaurantOrdersLabel}</dd>
        </div>
      </dl>
    </div>
  );
}
