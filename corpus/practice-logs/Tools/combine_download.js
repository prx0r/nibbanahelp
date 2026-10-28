/* HAND-OFF — run ONCE per capture run, in a FRESH Claude-in-Chrome TAB that is on the
   same origin the payloads were captured from (dharmaoverground.org for DhO threads).
   Bundles every cap_* payload stashed in localStorage into a single JSON and triggers
   ONE blob download to the browser's Downloads folder, which the sandbox reads.

   WHY A FRESH TAB + ONE DOWNLOAD:
   Chrome allows the FIRST automatic download in a tab, then silently blocks the rest
   (its "allow multiple automatic downloads?" gate). Opening a new tab resets that
   allowance, and localStorage is shared across tabs of the same origin, so the fresh
   tab still sees all the captured payloads. Doing exactly ONE combined download per run
   therefore always lands. (Verified: 6 awakenetwork parts = 385 KB, one file, clean.)

   Then in the sandbox:
     python3 Tools/process_payload.py <Downloads>/dho_capture.json "Data/DhO Practice Logs Board <date>"
   process_payload.py accepts EITHER a single {title,url,messages} payload OR a
   {key: payload, ...} bundle produced here.
*/
(() => {
  const bundle = {};
  const report = {};
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    if (k && k.startsWith('cap_')) {
      const v = localStorage.getItem(k);
      bundle[k] = v;               // value is a JSON string; process_payload re-parses
      report[k] = v.length;
    }
  }
  const keys = Object.keys(bundle);
  if (!keys.length) return JSON.stringify({ error: 'no cap_* payloads in localStorage' });
  const blob = new Blob([JSON.stringify(bundle)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'dho_capture.json';
  document.body.appendChild(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 2000);
  return JSON.stringify({ triggered: true, count: keys.length, sizes: report });
})()
