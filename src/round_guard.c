/* Freestanding x64 payload. No imports, entry point, networking or allocation.
   Uses the original script's registered expression and event bindings. */
typedef unsigned char u8;
typedef unsigned int u32;
typedef unsigned long long u64;
void *memset(void *destination,int value,u64 count);
#pragma function(memset)
void *memset(void *destination,int value,u64 count) {
    volatile u8 *p=(volatile u8 *)destination;
    while (count--) *p++=(u8)value;
    return destination;
}
typedef void (*Expression)(void *, void *, void *, void *);
typedef void (*Getter)(void *, u32, void *);
typedef u64 (*Execute)(u64 *);
typedef void (*Dispatch)(void *, u64 *);
extern char __ImageBase;
#define EXPORT __declspec(dllexport)
#define NONE (~(u64)0)
#define TRUE_EDGE 0x56ccd1bd99a59d3bULL
#define FALSE_EDGE 0x54dc9983c968aa39ULL
#define WATCH_NODE 0x70644733ULL
typedef struct {
    u64 image_rva, kind, execute_rva, dispatch_rva;
    u64 symbol_expression, symbol_getter, symbol_slot;
    u64 net_expression, social_getter, social_slot;
} Configuration;
EXPORT volatile Configuration configuration = {0x5044475541524433ULL};
/* Summon requests from the DiscButton plugin (Oculus A button). The plugin finds
   this block by its magic in the disc actor DLL, stores the tick of the press
   (KUSER_SHARED_DATA TickCountQuad) and then increments presses. */
typedef struct { u64 magic, version, presses, consumed, press_tick; } Summon;
EXPORT volatile Summon summon = {0x4E4F5454554B5344ULL, 1, 0, 0, 0};
#define TICK_NOW (*(volatile u64 *)0x7FFE0320ULL)
#define SUMMON_MAX_AGE 64 /* ticks of ~15.6 ms: presses older than ~1 s are dropped */

static u8 *base(void) { return (u8 *)&__ImageBase - configuration.image_rva; }
static u8 *state(u64 *node) { return *(u8 **)(node[0]+0x68); }
static void empty_input(void *a,u64 b,u32 c,void *d) { (void)a;(void)b;(void)c;(void)d; }
static void symbol_input(u8 *context,u64 field,u32 type,void *out) {
    if (type==2) {
        if (field==0x96a9f88628a60b9bULL) *(u64 *)out=*(u64 *)(context+0x20);
        if (field==0xc8c33e48347213b5ULL) *(u64 *)out=*(u64 *)(context+0x28);
        if (field==0xe0b944dde1e8c893ULL) *(u64 *)out=*(u64 *)(context+0x18);
    } else if (type==4) {
        if (field==0xb7776d5425565bc2ULL) *(u8 *)out=context[0x30]!=0;
        if (field==0x305ac747079d9217ULL) *(u8 *)out=context[0x10]!=0;
    }
}
static u64 read_symbol(u64 *node,u64 symbol) {
    u8 *b=base();
    Expression expression=*(Expression *)(b+configuration.symbol_expression);
    Getter getter=*(Getter *)(b+configuration.symbol_getter);
    u64 context[7]={0};
    u64 scratch[100];
    u64 value=NONE;
    if (!expression || !getter) return NONE;
    context[0]=(u64)node;
    context[1]=NONE;
    context[3]=context[4]=NONE;
    context[5]=symbol;
    expression(node,scratch,context,symbol_input);
    getter(scratch,*(u32 *)(b+configuration.symbol_slot),&value);
    return value;
}
static int social(u64 *node) {
    u8 *b=base();
    Expression expression=*(Expression *)(b+configuration.net_expression);
    Getter getter=*(Getter *)(b+configuration.social_getter);
    u64 context[49]={0};
    u64 scratch[100];
    u8 value=0;
    if (!expression || !getter) return 0;
    context[0]=(u64)node;
    expression(node,scratch,context,empty_input);
    getter(scratch,*(u32 *)(b+configuration.social_slot),&value);
    return value!=0;
}
EXPORT int policy(u64 is_social,u64 game_state,u64 paused_state) {
    if (is_social) return 1;
    if (game_state==NONE || game_state==0) return 0;
    /* A requested timeout is not a timeout yet. Deny again on unpause. */
    if (paused_state==0x41d2d73c0f30021aULL) return 1;
    switch (game_state) {
        case 0x6c19a96227539facULL: /* pre_match_enter */
        case 0x3979ba686488ba64ULL: /* pre_match_wait_for_ready_enter */
        case 0xd69cc3ed9f1e31bfULL: /* pre_match_wait_for_ready_update */
        case 0xccea96e48128f05eULL: /* round_over_enter */
        case 0x67e1e232f03be11dULL: /* round_over_update */
        case 0x6077aa3dc058f5dcULL: /* post_round_wait_enter */
        case 0x9567032e22cdc734ULL: /* post_match_celebration_enter */
        case 0xf83fcdbb25ba6f07ULL: /* post_match_celebration_update */
        case 0x344d080ea700b7eaULL: /* personal_stats_enter */
        case 0x3eda28aae966fa2dULL: /* personal_stats_update */
        case 0xfc6140cc02f9c63dULL: /* waiting_to_return_to_lobby */
        /* Dead time from a goal until the tunnel opens. main_loop (play)
           follows pre_launch, so the watcher disables (and hides the disc)
           as the tunnel opens. */
        case 0x56edca9065f29296ULL: /* point_score_enter */
        case 0x75c7a4739d7a1739ULL: /* point_score_update */
        case 0xf9162deb27723fa6ULL: /* post_score_replay_enter */
        case 0xc3d1fdd40bb69c3fULL: /* post_score_replay_update */
        /* "Get to your launcher": after the replay (and before each round) the
           game waits in team_room_wait, whose enter sends nevt_disable_local_disc.
           Allowed, so that disable is blocked and the disc stays out. */
        case 0xe1c16321def4cc6cULL: /* team_room_wait_enter */
        case 0xfbc46082c080fbcfULL: /* team_room_wait_update */
        case 0x51df52642db67278ULL: /* transition_to_launch_enter */
        case 0x97d0a383527c012fULL: /* transition_to_launch_update */
        case 0x37756d8877ed5768ULL: /* pre_launch_enter */
        case 0x7b54c48fed3ecd93ULL: /* pre_launch_update */
            return 1;
        default: return 0; /* Includes round_start, main_loop play and overtime. */
    }
}
static int allowed(u64 *node) {
    if (social(node)) return 1;
    return policy(0,read_symbol(node,0xb2996ad399fdc0ffULL),
                    read_symbol(node,0x02fe0aa4f2637309ULL));
}
static void request(u64 *node,u64 event) {
    u8 *s=state(node);
    u64 args[7];
    args[0]=event;
    args[1]=*(u64 *)(s+0x28);
    args[2]=*(u64 *)(s+0x30);
    args[3]=args[4]=*(u64 *)(s+0x38);
    args[5]=args[6]=NONE;
    ((Dispatch)(base()+configuration.dispatch_rva))((void *)node[0],args);
}
EXPORT u64 controller_execute(u64 *node) {
    u64 id=node[2];
    u8 *s=state(node);
    if (id==WATCH_NODE) {
        u8 *instance=(u8 *)node[0];
        if (instance[0x60] || instance[0x62] || s[0x27]) return 0; /* cancellation/quit */
        int permit=allowed(node);
        if (permit && !s[0x24]) request(node,0x0de861be446aaa7fULL);
        if (!permit && s[0x24]) request(node,0x50810c0485ce64efULL);
        return NONE; /* Persistent normal-update thread, not a busy loop. */
    }
    if (id==0xa2cd46c0ULL) s[0x27]=1; /* Don't recreate the control during quit. */
    if (id==0x57b5c17eULL || id==0x5ab76adcULL || id==0x5e7f5836ULL) {
        if (s[0x27] || !allowed(node)) { node[2]=0; return 0; }
    }
    /* Zone exit/round requests cannot disable an allowed timeout/lobby. */
    if (id==0x9f827e82ULL && allowed(node)) { node[2]=0; return 0; }
    /* No arm popup: 0x9d959ce0 shows "PERSONAL DISC" (its event summons the disc)
       on enable, 0x49eb587d runs on disable. The DiscButton A button replaces it. */
    if (id==0x9d959ce0ULL || id==0x49eb587dULL) return 0;
    if (id==0x204a9426ULL) {
        s[0x26]=(u8)(s[0x24] && allowed(node));
        return 0;
    }
    return ((Execute)(base()+configuration.execute_rva))(node);
}
EXPORT u64 disc_execute(u64 *node) {
    u8 *s=state(node);
    if (s[0xa7] && !allowed(node)) {
        s[0xa8]=0; /* Discard a queued teleport/respawn request. */
        /* A request can already be waiting for can_teleport when play resumes.
           Return that thread to the request check instead of deferring a spawn. */
        if (node[2]==0x048a9d90ULL) {
            node[2]=0x417c26abULL;
            return NONE;
        }
        if (node[2]==0xa527ed59ULL || node[2]==0x97132931ULL) {
            node[2]=0;
            return 0;
        }
    }
    return ((Execute)(base()+configuration.execute_rva))(node);
}
EXPORT u64 disc_requested(u64 *node) {
    u8 *s=state(node);
    if (!s[0xa7]) return s[0xa8]; /* Not the local personal disc. */
    u64 presses=summon.presses;
    if (presses!=summon.consumed) {
        summon.consumed=presses;
        /* Same flag the arm popup's evt_respawn_local_disc sets (node 0x97132931). */
        if (TICK_NOW-summon.press_tick<=SUMMON_MAX_AGE && allowed(node)) s[0xa8]=1;
    }
    if (!allowed(node)) s[0xa8]=0;
    return s[0xa8];
}
EXPORT u64 disc_condition(u64 *node) {
    return disc_requested(node) ? TRUE_EDGE : FALSE_EDGE;
}
