import dou from "./assets/people/dou.jpg";
import able from "./assets/people/able.jpg";
import margaret from "./assets/people/margaret.jpg";
import harold from "./assets/people/harold.jpg";
import joyce from "./assets/people/joyce.jpg";
import ibrahim from "./assets/people/ibrahim.jpg";
import evelyn from "./assets/people/evelyn.jpg";
import frank from "./assets/people/frank.jpg";
import aisha from "./assets/people/aisha.jpg";
import george from "./assets/people/george.jpg";

const PHOTOS = {
  Dou: dou,
  Dad: dou,
  Able: able,
  Margaret: margaret,
  Harold: harold,
  Joyce: joyce,
  Ibrahim: ibrahim,
  Evelyn: evelyn,
  Frank: frank,
  Aisha: aisha,
  George: george,
};

export function personPhoto(name) {
  return PHOTOS[name] || "";
}
