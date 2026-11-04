/**
 * A banner that marks AI-generated content as a proposal awaiting human approval.
 * Every drafting/approval surface shows it so the human-in-the-loop boundary is
 * explicit (design §8).
 */
export function ProposalBanner({ note }: { note?: string }) {
  return (
    <div className="mb-4 rounded-md border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-sm text-amber-200">
      <span className="font-semibold">AI proposal · </span>
      {note ?? 'Review before any action is taken. Nothing is submitted without explicit approval.'}
    </div>
  )
}
