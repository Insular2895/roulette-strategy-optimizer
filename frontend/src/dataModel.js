export function buildOutcomes(strategy) {
  const totalStaked = strategy.metrics.total_staked;
  return Array.from({ length: 37 }, (_, number) => {
    const winningBets = strategy.bets.filter((bet) => bet.numbers.includes(number));
    const grossReturn = winningBets.reduce((sum, bet) => sum + bet.stake * (bet.payout + 1), 0);
    const netProfit = grossReturn - totalStaked;
    return {
      number,
      gross_return: grossReturn,
      net_profit: netProfit,
      is_covered: winningBets.length > 0,
      is_profitable: netProfit > 0,
      is_big_hit: netProfit >= 100,
      winning_bets: winningBets,
      explanation: winningBets.length
        ? `Stacked payouts from ${winningBets.map((bet) => bet.type).join(', ')}.`
        : 'No covered bet wins on this number.',
    };
  });
}

export function buildMonteCarloPaths(outcomes, stake) {
  const sessions = Array.from({ length: 24 }, (_, session) => {
    let bankroll = 100;
    const points = [{ spin: 0, bankroll }];
    for (let spin = 1; spin <= 80; spin += 1) {
      const index = (session * 17 + spin * 11 + spin * session) % outcomes.length;
      bankroll = Math.max(0, bankroll + outcomes[index].net_profit);
      if (bankroll < stake) {
        bankroll = Math.max(0, bankroll - 0.2);
      }
      points.push({ spin, bankroll });
    }
    return { id: `session-${session}`, points };
  });

  const average = {
    id: 'average',
    average: true,
    points: sessions[0].points.map((point, index) => ({
      spin: point.spin,
      bankroll: sessions.reduce((sum, session) => sum + session.points[index].bankroll, 0) / sessions.length,
    })),
  };

  return [...sessions, average];
}
