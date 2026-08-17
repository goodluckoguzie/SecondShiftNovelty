import { Avatar } from "../components/Avatar.jsx";
import { PageHeader } from "../components/PageHeader.jsx";

export function PeopleScreen({ people, assignedPersonId, onOpenPerson }) {
  const ordered = [...(people || [])].sort((a, b) => {
    if (a.id === assignedPersonId) return -1;
    if (b.id === assignedPersonId) return 1;
    return (a.name || "").localeCompare(b.name || "");
  });

  return (
    <section className="space-y-4">
      <PageHeader title="People" hint="Tap a name to speak about them." />
      <ul className="space-y-3">
        {ordered.map((person) => (
          <li key={person.id}>
            <button type="button" className="tap-card w-full text-left" onClick={() => onOpenPerson(person)}>
              <span className="flex items-center gap-3">
                <Avatar name={person.name} size="lg" />
                <span>
                  <span className="block text-xl font-bold">{person.name}</span>
                  {person.id === assignedPersonId ? <span className="text-base font-bold text-accent">Yours</span> : null}
                </span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
