import { ProfileView } from '../accountModel';

/**
 * What EasyOrder has learned about how you order.
 *
 * Shown so a learned default is inspectable rather than mysterious: the same
 * values the agent fills in when a WhatsApp prompt leaves them unsaid. Below
 * the confidence threshold it renders greyed with a countdown, so the page
 * never implies a preference is in use before it is.
 */
export function ProfileCard({ profile }: { profile: ProfileView }) {
  if (profile.isEmpty || profile.traits.length === 0) return null;

  return (
    <div
      className={`profile-card ${profile.isConfident ? '' : 'profile-card--pending'}`}
      aria-label="What EasyOrder has learned"
    >
      <div className="profile-header">
        <p className="profile-label">Your usual</p>
        <p className="profile-headline">{profile.headline}</p>
      </div>
      <dl className="profile-traits">
        {profile.traits.map((trait) => (
          <div key={trait.label}>
            <dt>{trait.label}</dt>
            <dd>{trait.value}</dd>
          </div>
        ))}
      </dl>
      <p className="profile-footnote">
        EasyOrder fills these in when your message doesn&apos;t say. Say it in the message to
        override.
      </p>
    </div>
  );
}
