/* RO Emotes — data + picker + rendering for shoutbox */
var RO_EMOTES = [
    { cmd: '/!',    file: 'Exc.gif',    name: 'Surprise' },
    { cmd: '/?',    file: 'Que.gif',    name: 'Question' },
    { cmd: '/ho',   file: 'Hoe.gif',    name: 'Music' },
    { cmd: '/lv',   file: 'Lov.gif',    name: 'Love' },
    { cmd: '/lv2',  file: 'Lov2.gif',   name: 'Love2' },
    { cmd: '/swt',  file: 'Swt.gif',    name: 'Sweat' },
    { cmd: '/ic',   file: 'Lit.gif',    name: 'Idea' },
    { cmd: '/an',   file: 'Ang.gif',    name: 'Angry' },
    { cmd: '/ag',   file: 'Agh.gif',    name: 'Frustrated' },
    { cmd: '/$',    file: 'Money.gif',  name: 'Money' },
    { cmd: '/...',  file: 'Dots.gif',   name: 'Dots' },
    { cmd: '/thx',  file: 'Thx.gif',    name: 'Thanks' },
    { cmd: '/wah',  file: 'Wah.gif',    name: 'Crying' },
    { cmd: '/sry',  file: 'Sry.gif',    name: 'Sorry' },
    { cmd: '/heh',  file: 'Heh.gif',    name: 'Heh' },
    { cmd: '/swt2', file: 'Swt2.gif',   name: 'Sweat2' },
    { cmd: '/hmm',  file: 'Hmm.gif',    name: 'Hmm' },
    { cmd: '/no1',  file: 'No1.gif',    name: 'No1' },
    { cmd: '/ok',   file: 'Ok.gif',     name: 'OK' },
    { cmd: '/omg',  file: 'Omg.gif',    name: 'OMG' },
    { cmd: '/oh',   file: 'Ohh.gif',    name: 'Oh' },
    { cmd: '/X',    file: 'Ecks.gif',   name: 'Wrong' },
    { cmd: '/hlp',  file: 'Hlp.gif',    name: 'Help' },
    { cmd: '/go',   file: 'Goo.gif',    name: 'Go' },
    { cmd: '/sob',  file: 'Sob.gif',    name: 'Sob' },
    { cmd: '/gg',   file: 'Ggg.gif',    name: 'GG' },
    { cmd: '/kis',  file: 'Kis.gif',    name: 'Kiss' },
    { cmd: '/kis2', file: 'Kis2.gif',   name: 'Kiss2' },
    { cmd: '/pif',  file: 'Pif.gif',    name: 'Pif' },
    { cmd: '/??',   file: 'Ono.gif',    name: 'Confused' },
    { cmd: '/bzz',  file: 'Bzz.gif',    name: 'Buzz' },
    { cmd: '/rice', file: 'Rice.gif',   name: 'Rice' },
    { cmd: '/awsm', file: 'Awsm.gif',  name: 'Awesome' },
    { cmd: '/meh',  file: 'Meh.gif',    name: 'Meh' },
    { cmd: '/shy',  file: 'Shy.gif',    name: 'Shy' },
    { cmd: '/pat',  file: 'Pat.gif',    name: 'Pat' },
    { cmd: '/mp',   file: 'Mep.gif',    name: 'Mep' },
    { cmd: '/slur', file: 'Slur.gif',   name: 'Slurp' },
    { cmd: '/com',  file: 'Come.gif',   name: 'Come' },
    { cmd: '/yawn', file: 'Yawn.gif',   name: 'Yawn' },
    { cmd: '/grat', file: 'Grat.gif',   name: 'Grats' },
    { cmd: '/hp',   file: 'Hep.gif',    name: 'Hep' },
    { cmd: '/fsh',  file: 'Fsh.gif',    name: 'Fish' },
    { cmd: '/spin', file: 'Spin.gif',   name: 'Spin' },
    { cmd: '/sigh', file: 'Sigh.gif',   name: 'Sigh' },
    { cmd: '/dum',  file: 'Dum.gif',    name: 'Dumb' },
    { cmd: '/crwd', file: 'Crwd.gif',   name: 'Crowd' },
    { cmd: '/desp', file: 'Desp.gif',   name: 'Despair' },
    { cmd: '/dice', file: 'Dice.gif',   name: 'Dice' },
    { cmd: '/e20',  file: 'E20.gif',    name: 'Emote20' },
    { cmd: '/hum',  file: 'Hum.gif',    name: 'Hum' },
    { cmd: '/abs',  file: 'Abs.gif',    name: 'Abs' },
    { cmd: '/oops', file: 'Oops.gif',   name: 'Oops' },
    { cmd: '/spit', file: 'Spit.gif',   name: 'Spit' },
    { cmd: '/ene',  file: 'Ene.gif',    name: 'Enemy' },
    { cmd: '/panic',file: 'Panic.gif',  name: 'Panic' },
    { cmd: '/whisp',file: 'Whisp.gif',  name: 'Whisper' },
    { cmd: '/bawi', file: 'Emote_bawi.png', name: 'Rock' },
    { cmd: '/bo',   file: 'Emote_bo.png',   name: 'Paper' },
    { cmd: '/gawi', file: 'Emote_gawi.png', name: 'Scissors' }
];

/* Build a lookup map: command → image path */
var RO_EMOTE_MAP = {};
RO_EMOTES.forEach(function (e) {
    RO_EMOTE_MAP[e.cmd] = '/static/emotes/' + e.file;
});

/**
 * Replace emote shortcodes in text with <img> tags.
 * Text must already be HTML-escaped BEFORE calling this.
 */
function renderEmotesInHtml(escapedHtml) {
    // Sort commands longest-first so /lv2 matches before /lv, /swt2 before /swt, etc.
    var sorted = RO_EMOTES.slice().sort(function (a, b) {
        return b.cmd.length - a.cmd.length;
    });
    sorted.forEach(function (e) {
        // Escape special regex chars in the command
        var escaped = e.cmd.replace(/([.*+?^${}()|[\]\\\/])/g, '\\$1');
        // Match the command as a standalone token (not part of a longer word)
        var re = new RegExp(escaped + '(?![a-zA-Z0-9])', 'g');
        escapedHtml = escapedHtml.replace(re,
            '<img src="/static/emotes/' + e.file + '" class="ro-emote" alt="' + e.cmd + '" title="' + e.cmd + ' ' + e.name + '">');
    });
    return escapedHtml;
}
