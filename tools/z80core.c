/* z80core.c - minimal ZX Spectrum 48K emulator core for headless testing.
 * Documented Z80 instruction set (no IX/IY: any DD/FD prefix is reported as
 * an error so we notice). IM1/IM2 frame interrupts, keyboard half-rows,
 * Kempston port $1F, beeper/border on port $FE, approximate memory contention.
 * Driven from Python via ctypes (see spectest.py).
 */
#include <stdint.h>
#include <string.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;

static u8 mem[65536];
static u8 A,F,B,C,D,E,H,L, A_,F_,B_,C_,D_,E_,H_,L_, I,R;
static u16 SP,PC;
static int IFF1,IFF2,IM,halted;
static long T;
static int err; static u16 errpc; static u8 errop;
static u8 keyrows[8];
static u8 kempston;
static int border, beeps, beepstate;
static long halt_t;
static long frame_no;
static u8 sz53[256], sz53p[256];
static const u8 cdelay[8]={6,5,4,3,2,1,0,0};

#define FC 0x01
#define FN 0x02
#define FPV 0x04
#define F3 0x08
#define FH 0x10
#define F5 0x20
#define FZ 0x40
#define FS 0x80
#define FRAME 69888

static inline void contend(u16 a){
  if ((a & 0xC000) == 0x4000) {
    long t = T - 14335;
    if (t >= 0 && t < 192*224) { int p = t % 224; if (p < 128) T += cdelay[p & 7]; }
  }
}
static inline u8 rd(u16 a){ contend(a); return mem[a]; }
static inline void wr(u16 a, u8 v){ contend(a); if (a >= 0x4000) mem[a] = v; }
static inline u16 rd16(u16 a){ return rd(a) | (rd((u16)(a+1)) << 8); }
static inline void wr16(u16 a, u16 v){ wr(a, v & 0xFF); wr((u16)(a+1), v >> 8); }
static inline u8 fetch(void){ return mem[PC++]; }
static inline u16 fetch16(void){ u16 v = mem[PC] | (mem[(u16)(PC+1)] << 8); PC += 2; return v; }
static inline void push(u16 v){ SP -= 2; wr16(SP, v); }
static inline u16 pop(void){ u16 v = rd16(SP); SP += 2; return v; }

static u8 port_in(u16 port){
  if ((port & 0xFF) == 0x1F) return kempston;
  if (!(port & 1)) {
    u8 r = 0x1F; u8 hi = port >> 8;
    for (int i = 0; i < 8; i++) if (!(hi & (1 << i))) r &= keyrows[i];
    return r | 0xA0;
  }
  return 0xFF;
}
static void port_out(u16 port, u8 v){
  if (!(port & 1)) { border = v & 7; int b = (v >> 4) & 1; if (b != beepstate) { beeps++; beepstate = b; } }
}

#define BC_ ((B<<8)|C)
#define DE_ ((D<<8)|E)
#define HL_ ((H<<8)|L)
#define SETBC(v) do{u16 _v=(v);B=_v>>8;C=_v&0xFF;}while(0)
#define SETDE(v) do{u16 _v=(v);D=_v>>8;E=_v&0xFF;}while(0)
#define SETHL(v) do{u16 _v=(v);H=_v>>8;L=_v&0xFF;}while(0)

static void add8(u8 v, int c){ u32 r = A + v + c; F = ((r>>8)&1) | ((A^v^r)&FH) | ((((A^~v)&(A^r))&0x80)?FPV:0) | sz53[r&0xFF]; A = r; }
static void sub8(u8 v, int c){ u32 r = (u32)A - v - c; F = ((r>>8)&1) | FN | ((A^v^r)&FH) | ((((A^v)&(A^r))&0x80)?FPV:0) | sz53[r&0xFF]; A = r; }
static void cp8(u8 v){ u8 a = A; sub8(v, 0); A = a; F = (F & ~(F3|F5)) | (v & (F3|F5)); }
static void alu(int op, u8 v){
  switch(op){
    case 0: add8(v,0); break; case 1: add8(v,F&FC); break;
    case 2: sub8(v,0); break; case 3: sub8(v,F&FC); break;
    case 4: A &= v; F = sz53p[A] | FH; break;
    case 5: A ^= v; F = sz53p[A]; break;
    case 6: A |= v; F = sz53p[A]; break;
    case 7: cp8(v); break;
  }
}
static u8 inc8(u8 v){ u8 r = v+1; F = (F&FC) | (r==0x80?FPV:0) | ((r&0x0F)==0?FH:0) | sz53[r]; return r; }
static u8 dec8(u8 v){ u8 r = v-1; F = (F&FC) | FN | (v==0x80?FPV:0) | ((v&0x0F)==0?FH:0) | sz53[r]; return r; }
static u16 add16(u16 a, u16 b){ u32 r = a + b; F = (F&(FS|FZ|FPV)) | ((r>>16)&1) | (((a^b^r)>>8)&FH) | ((r>>8)&(F3|F5)); return r; }
static u16 adc16(u16 a, u16 b){ u32 r = a + b + (F&FC); F = ((r>>16)&1) | (((a^b^r)>>8)&FH) | ((((a^~b)&(a^r))&0x8000)?FPV:0) | ((r>>8)&(FS|F3|F5)) | ((r&0xFFFF)?0:FZ); return r; }
static u16 sbc16(u16 a, u16 b){ u32 r = (u32)a - b - (F&FC); F = FN | ((r>>16)&1) | (((a^b^r)>>8)&FH) | ((((a^b)&(a^r))&0x8000)?FPV:0) | ((r>>8)&(FS|F3|F5)) | ((r&0xFFFF)?0:FZ); return r; }

static u8 getr(int r){
  switch(r){case 0:return B;case 1:return C;case 2:return D;case 3:return E;case 4:return H;case 5:return L;case 6:return rd(HL_);default:return A;}
}
static void setr(int r, u8 v){
  switch(r){case 0:B=v;break;case 1:C=v;break;case 2:D=v;break;case 3:E=v;break;case 4:H=v;break;case 5:L=v;break;case 6:wr(HL_,v);break;default:A=v;}
}
static u16 getrp(int p){ switch(p){case 0:return BC_;case 1:return DE_;case 2:return HL_;default:return SP;} }
static void setrp(int p, u16 v){ switch(p){case 0:SETBC(v);break;case 1:SETDE(v);break;case 2:SETHL(v);break;default:SP=v;} }
static int cond(int c){
  switch(c){case 0:return !(F&FZ);case 1:return F&FZ;case 2:return !(F&FC);case 3:return F&FC;
  case 4:return !(F&FPV);case 5:return F&FPV;case 6:return !(F&FS);default:return F&FS;}
}

static void do_cb(void){
  u8 op = fetch(); R = (R&0x80)|((R+1)&0x7F);
  int r = op & 7, b = (op >> 3) & 7; u8 v = getr(r), res;
  switch(op >> 6){
  case 0:
    switch(b){
      case 0: res=(v<<1)|(v>>7); F=sz53p[res]|(v>>7); break;
      case 1: res=(v>>1)|(v<<7); F=sz53p[res]|(v&1); break;
      case 2: res=(v<<1)|(F&FC); F=sz53p[res]|(v>>7); break;
      case 3: res=(v>>1)|((F&FC)<<7); F=sz53p[res]|(v&1); break;
      case 4: res=v<<1; F=sz53p[res]|(v>>7); break;
      case 5: res=(v>>1)|(v&0x80); F=sz53p[res]|(v&1); break;
      case 6: res=(v<<1)|1; F=sz53p[res]|(v>>7); break;
      default: res=v>>1; F=sz53p[res]|(v&1); break;
    }
    setr(r,res); T += (r==6)?15:8; break;
  case 1:
    F = (F&FC) | FH | (v&(F3|F5));
    if (!(v & (1<<b))) F |= FPV|FZ;
    if (b==7 && (v&0x80)) F |= FS;
    T += (r==6)?12:8; break;
  case 2: setr(r, v & ~(1<<b)); T += (r==6)?15:8; break;
  default: setr(r, v | (1<<b)); T += (r==6)?15:8; break;
  }
}

static void bad(u8 op){ err = 1; errpc = PC; errop = op; }

static void do_ed(void){
  u8 op = fetch(); R = (R&0x80)|((R+1)&0x7F);
  int p = (op>>4)&3, r = (op>>3)&7; u8 v;
  if (op >= 0x40 && op < 0x80) {
    switch(op & 7){
      case 0: v = port_in(BC_); if (r!=6) setr(r,v); F=(F&FC)|sz53p[v]; T+=12; return;
      case 1: port_out(BC_, r==6?0:getr(r)); T+=12; return;
      case 2: if (op & 8) SETHL(adc16(HL_, getrp(p))); else SETHL(sbc16(HL_, getrp(p))); T+=15; return;
      case 3: { u16 a = fetch16(); if (op & 8) setrp(p, rd16(a)); else wr16(a, getrp(p)); T+=20; return; }
      case 4: v=A; A=0; sub8(v,0); T+=8; return;
      case 5: IFF1=IFF2; PC=pop(); T+=14; return;
      case 6: IM = (r&3)==0?0:((r&3)==2?1:2); if ((r&3)==1) IM=0; T+=8; return;
      case 7:
        switch(r){
          case 0: I=A; T+=9; return;
          case 1: R=A; T+=9; return;
          case 2: A=I; F=(F&FC)|sz53[A]|(IFF2?FPV:0); T+=9; return;
          case 3: A=R; F=(F&FC)|sz53[A]|(IFF2?FPV:0); T+=9; return;
          case 4: { u8 m=rd(HL_); wr(HL_, (A<<4)|(m>>4)); A=(A&0xF0)|(m&0x0F); F=(F&FC)|sz53p[A]; T+=18; return; } /* RRD */
          case 5: { u8 m=rd(HL_); wr(HL_, (m<<4)|(A&0x0F)); A=(A&0xF0)|(m>>4); F=(F&FC)|sz53p[A]; T+=18; return; } /* RLD */
          default: T+=8; return;
        }
    }
  }
  switch(op){
    case 0xA0: case 0xB0: case 0xA8: case 0xB8: {
      int dir = (op & 8) ? -1 : 1;
      v = rd(HL_); wr(DE_, v); SETHL(HL_+dir); SETDE(DE_+dir); SETBC(BC_-1);
      F = (F&(FS|FZ|FC)) | (BC_?FPV:0);
      if ((op & 0x10) && BC_) { PC -= 2; T += 21; } else T += 16;
      return; }
    case 0xA1: case 0xB1: case 0xA9: case 0xB9: {
      int dir = (op & 8) ? -1 : 1;
      v = rd(HL_); u8 res = A - v; SETHL(HL_+dir); SETBC(BC_-1);
      F = (F&FC) | FN | (sz53[res]&~(F3|F5)) | ((A^v^res)&FH) | (BC_?FPV:0);
      if ((op & 0x10) && BC_ && res) { PC -= 2; T += 21; } else T += 16;
      return; }
  }
  bad(op);
}

static void interrupt(void){
  if (!IFF1) return;
  if (halted) { halted = 0; PC++; }
  IFF1 = IFF2 = 0;
  push(PC);
  if (IM == 2) { PC = rd16((I<<8)|0xFF); T += 19; }
  else { PC = 0x38; T += 13; }
}

static void step(void){
  u8 op = fetch(); R = (R&0x80)|((R+1)&0x7F);
  int x = op>>6, y = (op>>3)&7, z = op&7, p = y>>1, q = y&1;
  if (x == 1) {
    if (op == 0x76) { halted = 1; PC--; T += 4; return; }
    setr(y, getr(z)); T += (y==6||z==6)?7:4; return;
  }
  if (x == 2) { alu(y, getr(z)); T += (z==6)?7:4; return; }
  if (x == 0) {
    switch(z){
    case 0:
      switch(y){
        case 0: T+=4; return;
        case 1: { u8 t; t=A;A=A_;A_=t; t=F;F=F_;F_=t; T+=4; return; }
        case 2: { int8_t d = fetch(); B--; if (B) { PC += d; T+=13; } else T+=8; return; }
        case 3: { int8_t d = fetch(); PC += d; T+=12; return; }
        default: { int8_t d = fetch(); if (cond(y-4)) { PC += d; T+=12; } else T+=7; return; }
      }
    case 1:
      if (!q) { setrp(p, fetch16()); T+=10; } else { SETHL(add16(HL_, getrp(p))); T+=11; } return;
    case 2:
      switch(y){
        case 0: wr(BC_, A); T+=7; return;
        case 1: A = rd(BC_); T+=7; return;
        case 2: wr(DE_, A); T+=7; return;
        case 3: A = rd(DE_); T+=7; return;
        case 4: wr16(fetch16(), HL_); T+=16; return;
        case 5: SETHL(rd16(fetch16())); T+=16; return;
        case 6: wr(fetch16(), A); T+=13; return;
        default: A = rd(fetch16()); T+=13; return;
      }
    case 3: if (!q) setrp(p, getrp(p)+1); else setrp(p, getrp(p)-1); T+=6; return;
    case 4: setr(y, inc8(getr(y))); T += (y==6)?11:4; return;
    case 5: setr(y, dec8(getr(y))); T += (y==6)?11:4; return;
    case 6: setr(y, fetch()); T += (y==6)?10:7; return;
    default:
      switch(y){
        case 0: A=(A<<1)|(A>>7); F=(F&(FS|FZ|FPV))|(A&(FC|F3|F5)); break;
        case 1: F=(F&(FS|FZ|FPV))|(A&FC); A=(A>>1)|(A<<7); F|=A&(F3|F5); break;
        case 2: { u8 c=A>>7; A=(A<<1)|(F&FC); F=(F&(FS|FZ|FPV))|c|(A&(F3|F5)); break; }
        case 3: { u8 c=A&1; A=(A>>1)|((F&FC)<<7); F=(F&(FS|FZ|FPV))|c|(A&(F3|F5)); break; }
        case 4: { u8 add=0, c=F&FC, h;
          if ((F&FH) || (A&0x0F)>9) add=6;
          if (c || A>0x99) { add|=0x60; c=1; }
          if (F&FN) { h = (F&FH) && (A&0x0F)<6; A-=add; } else { h = (A&0x0F)>9; A+=add; }
          F=(F&FN)|c|(h?FH:0)|sz53p[A]; break; }
        case 5: A^=0xFF; F=(F&(FS|FZ|FPV|FC))|FH|FN|(A&(F3|F5)); break;
        case 6: F=(F&(FS|FZ|FPV))|FC|(A&(F3|F5)); break;
        default: F=(F&(FS|FZ|FPV))|((F&FC)?FH:FC)|(A&(F3|F5)); break;
      }
      T+=4; return;
    }
  }
  /* x == 3 */
  switch(z){
  case 0: if (cond(y)) { PC=pop(); T+=11; } else T+=5; return;
  case 1:
    if (!q) { u16 v=pop(); if (p==3) { A=v>>8; F=v&0xFF; } else setrp(p, v); T+=10; return; }
    switch(p){
      case 0: PC=pop(); T+=10; return;
      case 1: { u8 t; t=B;B=B_;B_=t; t=C;C=C_;C_=t; t=D;D=D_;D_=t; t=E;E=E_;E_=t; t=H;H=H_;H_=t; t=L;L=L_;L_=t; T+=4; return; }
      case 2: PC=HL_; T+=4; return;
      default: SP=HL_; T+=6; return;
    }
  case 2: { u16 a=fetch16(); if (cond(y)) PC=a; T+=10; return; }
  case 3:
    switch(y){
      case 0: PC=fetch16(); T+=10; return;
      case 1: do_cb(); return;
      case 2: { u8 n=fetch(); port_out((A<<8)|n, A); T+=11; return; }
      case 3: { u8 n=fetch(); A=port_in((A<<8)|n); T+=11; return; }
      case 4: { u16 v=rd16(SP); wr16(SP, HL_); SETHL(v); T+=19; return; }
      case 5: { u8 t; t=D;D=H;H=t; t=E;E=L;L=t; T+=4; return; }
      case 6: IFF1=IFF2=0; T+=4; return;
      default: IFF1=IFF2=1; T+=4; return;
    }
  case 4: { u16 a=fetch16(); if (cond(y)) { push(PC); PC=a; T+=17; } else T+=10; return; }
  case 5:
    if (!q) { u16 v = (p==3) ? ((A<<8)|F) : getrp(p); push(v); T+=11; return; }
    switch(p){
      case 0: { u16 a=fetch16(); push(PC); PC=a; T+=17; return; }
      case 2: do_ed(); return;
      default: bad(op); return;
    }
  case 6: alu(y, fetch()); T+=7; return;
  default: push(PC); PC=y*8; T+=11; return;
  }
}

void z_init(void){
  for (int i=0;i<256;i++){
    u8 s = (i & (FS|F3|F5)) | (i==0?FZ:0);
    int par=1; for (int b=0;b<8;b++) if (i&(1<<b)) par^=1;
    sz53[i]=s; sz53p[i]=s|(par?FPV:0);
  }
  memset(mem, 0, sizeof mem);
  /* fake ROM: IM1 handler = EI; RET */
  memset(mem, 0xFF, 0x4000);
  mem[0x38]=0xFB; mem[0x39]=0xC9;
  memset(keyrows, 0x1F, 8);
  kempston = 0; err = 0; T = 0; halted = 0; frame_no = 0;
  A=F=B=C=D=E=H=L=0xFF; SP=0xFF40; PC=0; I=0x3F; R=0; IFF1=IFF2=1; IM=1;
}
void z_setpc(int pc){ PC = pc; halted = 0; }
void z_setsp(int sp){ SP = sp; }
int z_getpc(void){ return PC; }
u8 *z_mem(void){ return mem; }
void z_key(int row, int bit, int down){ if (down) keyrows[row] &= ~(1<<bit); else keyrows[row] |= (1<<bit); }
void z_kempston(int v){ kempston = v; }
int z_err(void){ return err; }
int z_errpc(void){ return errpc; }
int z_errop(void){ return errop; }
int z_border(void){ return border; }
long z_halt_t(void){ return halt_t; }
int z_beeps(void){ int b = beeps; beeps = 0; return b; }

/* Run one 50Hz frame. Returns 0 ok, 1 error. halt_t = T-state of first HALT
 * in the frame (how much of the frame the game used), -1 if none. */
static int nwatch; static u16 watch[16]; static long watch_t[16];
void z_watch(int i, int a){ watch[i] = a; if (i >= nwatch) nwatch = i+1; }
long z_watch_t(int i){ long t = watch_t[i]; watch_t[i] = -1; return t; }
int z_frame(void){
  interrupt();
  halt_t = -1;
  while (T < FRAME) {
    if (halted) { if (halt_t < 0) halt_t = T; T = FRAME; break; }
    for (int w = 0; w < nwatch; w++) if (PC == watch[w]) watch_t[w] = T;
    step();
    if (err) return 1;
  }
  T -= FRAME; frame_no++;
  return 0;
}

/* ---- save states (for the planning bot): everything that defines the machine */
#define SV(x) {&(x), sizeof(x)}
static struct { void *p; size_t n; } svtab[] = {
  SV(mem), SV(A),SV(F),SV(B),SV(C),SV(D),SV(E),SV(H),SV(L),
  SV(A_),SV(F_),SV(B_),SV(C_),SV(D_),SV(E_),SV(H_),SV(L_),SV(I),SV(R),
  SV(SP),SV(PC),SV(IFF1),SV(IFF2),SV(IM),SV(halted),SV(T),SV(keyrows),SV(kempston),
  SV(border),SV(beepstate),SV(frame_no) };
int z_state_size(void){ size_t n=0; for (unsigned i=0;i<sizeof svtab/sizeof svtab[0];i++) n+=svtab[i].n; return (int)n; }
void z_save(u8 *buf){ for (unsigned i=0;i<sizeof svtab/sizeof svtab[0];i++){ memcpy(buf, svtab[i].p, svtab[i].n); buf+=svtab[i].n; } }
void z_load(u8 *buf){ for (unsigned i=0;i<sizeof svtab/sizeof svtab[0];i++){ memcpy(svtab[i].p, buf, svtab[i].n); buf+=svtab[i].n; } }
void z_seta(int a){ A = a; }
