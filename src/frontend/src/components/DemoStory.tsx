import { useEffect, useMemo, useState } from 'react';

type Scene = {
  kicker: string;
  title: string;
  prompt: string;
  emoji: string;
  oldWay: string[];
  order: { name: string; qty: number; price: number }[];
  restaurant: string;
  note: string;
  total: number;
  budget?: number;
  eta: string;
};

const scenes: Scene[] = [
  {
    kicker: '01 · THE HOUSE PARTY',
    title: 'Seven opinions.\nOne sane order.',
    prompt:
      '2 Chicken Biryani, 1 Mixed Veg and 3 Tandoori Roti from the best places. Keep it under ₹2,000.',
    emoji: '🎉',
    oldWay: ['47 menus scrolled', '3 calculators opened', '“Who ordered veg?” × 6'],
    order: [
      { name: 'Chicken Biryani', qty: 2, price: 678 },
      { name: 'Mixed Veg', qty: 1, price: 289 },
      { name: 'Tandoori Roti', qty: 3, price: 147 },
    ],
    restaurant: 'Paradise + Moti Mahal',
    note: 'Best-rated match · everyone can edit',
    total: 1114,
    budget: 2000,
    eta: '32–38 min',
  },
  {
    kicker: '02 · THE BUDGET BOUNCER',
    title: 'Cravings in.\nRegret blocked.',
    prompt:
      'Paneer Tikka and Chicken 65 from Moti Mahal. If it crosses ₹800, ask me first.',
    emoji: '🛡️',
    oldWay: ['Restaurant hunted down', 'Menu archaeology', 'Budget remembered… hopefully'],
    order: [
      { name: 'Paneer Tikka', qty: 1, price: 449 },
      { name: 'Chicken 65', qty: 1, price: 429 },
    ],
    restaurant: 'Moti Mahal',
    note: '₹78 over budget · waiting for your YES',
    total: 878,
    budget: 800,
    eta: '28–34 min',
  },
  {
    kicker: '03 · FUTURE YOU SAYS THANKS',
    title: 'Dinner at eight.\nNoodles defeated.',
    prompt: 'Egg Biryani from Biryani By Kilo. Make sure it reaches me by 8 PM.',
    emoji: '⏰',
    oldWay: ['Set reminder', 'Ignore reminder', 'Meet instant noodles at 9:13'],
    order: [{ name: 'Hyderabadi Egg Biryani', qty: 1, price: 399 }],
    restaurant: 'Biryani By Kilo',
    note: 'EasyOrder will nudge you at the perfect time',
    total: 399,
    eta: 'Arrives 7:30–8:00',
  },
];

export function DemoStory() {
  const [sceneIndex, setSceneIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [phase, setPhase] = useState(0);
  const [role, setRole] = useState<'Host' | 'Guest'>('Host');
  const [quantities, setQuantities] = useState<number[]>(scenes[0].order.map((item) => item.qty));
  const [actionMessage, setActionMessage] = useState('');
  const scene = scenes[sceneIndex];

  useEffect(() => {
    setPhase(0);
    setQuantities(scenes[sceneIndex].order.map((item) => item.qty));
    setActionMessage('');
    const timers = [500, 1300, 2200].map((delay, index) =>
      window.setTimeout(() => setPhase(index + 1), delay),
    );
    return () => timers.forEach(window.clearTimeout);
  }, [sceneIndex]);

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => {
      setSceneIndex((current) => {
        if (current === scenes.length - 1) {
          setPlaying(false);
          return current;
        }
        return current + 1;
      });
    }, 7500);
    return () => window.clearInterval(timer);
  }, [playing]);

  const progress = useMemo(
    () => ((sceneIndex + (phase / 3) * 0.85) / scenes.length) * 100,
    [sceneIndex, phase],
  );
  const liveTotal = scene.order.reduce(
    (total, item, index) => total + (item.price / item.qty) * quantities[index],
    0,
  );
  const overBudget = scene.budget !== undefined && liveTotal > scene.budget;

  function updateQuantity(index: number, difference: number) {
    setQuantities((current) =>
      current.map((quantity, itemIndex) =>
        itemIndex === index ? Math.max(0, quantity + difference) : quantity,
      ),
    );
    setActionMessage(role === 'Guest' ? 'Guest edit synced for everyone ✓' : 'Session updated live ✓');
  }

  function completeAction() {
    setActionMessage(
      sceneIndex === 0
        ? 'Shared link copied — the group can verify and edit ✓'
        : sceneIndex === 1
          ? 'Approval request sent — no surprise spending ✓'
          : 'Dinner scheduled — instant noodles stood down ✓',
    );
  }

  function next() {
    setSceneIndex((current) => (current + 1) % scenes.length);
  }

  return (
    <main className="demo-story">
      <div className="demo-grain" />
      <header className="demo-header">
        <a className="demo-brand" href="/" aria-label="EasyOrder home">
          Easy<span>Order</span><i>●</i>
        </a>
        <div className="demo-header-center">
          <span>LIVE PRODUCT STORY</span>
          <b>{String(sceneIndex + 1).padStart(2, '0')} / 03</b>
        </div>
        <button
          className="demo-play"
          aria-pressed={playing}
          onClick={() => setPlaying((value) => !value)}
        >
          {playing ? '❚❚ Pause story' : '▶ Play quick story'}
        </button>
      </header>

      <div className="demo-progress"><span style={{ width: `${progress}%` }} /></div>

      <section className="demo-stage" key={sceneIndex}>
        <div className="demo-narrative">
          <p className="demo-kicker">{scene.kicker}</p>
          <h1>{scene.title.split('\n').map((line) => <span key={line}>{line}</span>)}</h1>
          <p className="demo-punchline">
            Ordering dinner should not feel like<br />filing your income tax.
          </p>

          <div className="demo-chaos">
            <div className="demo-chaos-title">
              <span className="demo-stress-face">{scene.emoji}</span>
              <div><small>THE OLD WAY</small><strong>Stress level: papad under pressure</strong></div>
            </div>
            {scene.oldWay.map((item, index) => (
              <p key={item} style={{ '--delay': `${index * 120}ms` } as React.CSSProperties}>
                <span>0{index + 1}</span>{item}
              </p>
            ))}
          </div>
        </div>

        <div className="demo-product">
          <div className="demo-phone-top">
            <div>
              <small>Party Command Centre</small>
              <strong>{['Saturday Night Survivors', 'Dinner for two', 'Dinner for one'][sceneIndex]}</strong>
            </div>
            <button onClick={() => setRole(role === 'Host' ? 'Guest' : 'Host')}>
              {role} ▾
            </button>
          </div>

          <div className={`demo-message ${phase >= 1 ? 'is-visible' : ''}`}>
            <span>VK</span><p>{scene.prompt}</p><time>7:08 PM ✓✓</time>
          </div>

          <div className={`demo-thinking ${phase === 1 ? 'is-visible' : ''}`}>
            <i /><i /><i /> EasyOrder is doing the menu maths…
          </div>

          <div className={`demo-receipt ${phase >= 2 ? 'is-visible' : ''}`}>
            <div className="demo-receipt-head">
              <div><small>SMART MATCH</small><strong>{scene.restaurant}</strong></div>
              <span>{scene.eta}</span>
            </div>
            <div className="demo-order-list">
              {scene.order.map((item, index) => (
                <div key={item.name}>
                  <b>{quantities[index]}×</b><span>{item.name}</span>
                  <span className="demo-quantity">
                    <button aria-label={`Remove one ${item.name}`} onClick={() => updateQuantity(index, -1)}>−</button>
                    <button aria-label={`Add one ${item.name}`} onClick={() => updateQuantity(index, 1)}>+</button>
                  </span>
                  <strong>₹{Math.round((item.price / item.qty) * quantities[index])}</strong>
                </div>
              ))}
            </div>
            <div className="demo-total">
              <span><small>LIVE TOTAL</small>₹{Math.round(liveTotal).toLocaleString('en-IN')}</span>
              {scene.budget && (
                <div className={overBudget ? 'is-over' : ''}>
                  <i style={{ width: `${Math.min((liveTotal / scene.budget) * 100, 100)}%` }} />
                  {overBudget ? `₹${Math.round(liveTotal - scene.budget)} over` : `₹${Math.round(scene.budget - liveTotal)} left`}
                </div>
              )}
            </div>
            <div className={`demo-status ${overBudget ? 'is-warning' : ''}`}>
              <span>{overBudget ? '!' : '✓'}</span>
              <p><strong>{overBudget ? 'Budget bouncer activated' : 'Everything understood'}</strong>{scene.note}</p>
            </div>
          </div>

          <button
            className={`demo-confirm ${phase >= 3 ? 'is-visible' : ''}`}
            disabled={phase < 3 || role === 'Guest'}
            onClick={completeAction}
          >
            {role === 'Guest'
              ? 'Guest edits are live · Host places order'
              : overBudget
                ? 'Review before ordering →'
                : sceneIndex === 2
                  ? 'Schedule my dinner →'
                  : 'Share with the group →'}
          </button>
          <p className={`demo-microcopy ${actionMessage ? 'has-action' : ''}`}>
            {actionMessage || 'No endless scrolls. No mental maths. No noodle emergencies.'}
          </p>
        </div>
      </section>

      <footer className="demo-footer">
        <div className="demo-scenes">
          {scenes.map((item, index) => (
            <button
              className={index === sceneIndex ? 'active' : ''}
              aria-current={index === sceneIndex ? 'step' : undefined}
              onClick={() => setSceneIndex(index)}
              key={item.kicker}
            >
              <span>0{index + 1}</span>{['Group order', 'Budget guardrail', 'Dinner scheduler'][index]}
            </button>
          ))}
        </div>
        <button className="demo-next" onClick={next}>Next scene <span>→</span></button>
      </footer>
    </main>
  );
}
