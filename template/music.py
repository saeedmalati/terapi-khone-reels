import numpy as np, wave, sys
SR=48000; DUR=24.0; N=int(SR*DUR)
rng=np.random.default_rng(7)
out=np.zeros((N,2))
def note_f(m): return 440*2**((m-69)/12)
def piano(m, t0, dur, vel, pan=0.0):
    f=note_f(m); n=int(SR*min(dur+2.5, DUR-t0)); 
    if n<=0: return
    t=np.arange(n)/SR
    env=np.exp(-t*(1.6+f/900))*(1-np.exp(-t*300))
    s=np.zeros(n)
    for k,a in enumerate([1,.5,.28,.14,.08,.04],1):
        s+=a*np.sin(2*np.pi*f*k*t*(1+0.0004*k*k))
    s*=env*vel
    i=int(t0*SR); e=min(N,i+n); s=s[:e-i]
    out[i:e,0]+=s*(1-pan)/1.4; out[i:e,1]+=s*(1+pan)/1.4
def pad(ms, t0, dur, vel):
    n=int(SR*dur); t=np.arange(n)/SR
    env=np.minimum(1,t/1.2)*np.minimum(1,(dur-t)/1.2)
    for j,m in enumerate(ms):
        f=note_f(m)
        for d,p in [(-0.12,-0.6),(0.12,0.6)]:
            ff=f*2**(d/12/10)
            s=(np.sin(2*np.pi*ff*t)+.3*np.sin(2*np.pi*2*ff*t)+.1*np.sin(2*np.pi*3*ff*t))*env*vel
            i=int(t0*SR); e=min(N,i+n)
            out[i:e,0]+=s[:e-i]*(1-p)/2; out[i:e,1]+=s[:e-i]*(1+p)/2
bpm=72; beat=60/bpm; bar=4*beat  # 3.333s per bar
# Am F C G | Am F C E -> resolve Am
prog=[(57,[57,60,64]),(53,[53,57,60]),(48,[52,55,60]),(55,[55,59,62]),
      (57,[57,60,64]),(53,[53,57,60]),(48,[52,55,60]),(52,[52,56,59])]
mel=[76,74,72,71, 72,71,69,67, 69,72,71,69, 67,64,62,64]
t=0.0; bi=0
while t< DUR-0.5 and bi< len(prog)+1:
    root,ch=prog[bi%len(prog)]
    pad([m-12 for m in ch],t,bar+0.6,0.035)
    piano(root-24,t,bar,0.33,0)
    # arpeggio
    arp=[ch[0],ch[1],ch[2],ch[1]+12 if False else ch[2]+5-5, ch[1]+12, ch[2], ch[1], ch[2]]
    for k in range(8):
        if bi==0 and k<1: pass
        piano(arp[k%len(arp)]+12 if k in(4,) else arp[k%len(arp)], t+k*beat/2, beat, 0.16+0.03*(k%2==0), -0.3+0.08*k)
    # melody from bar 2
    if bi>=1:
        for k in range(2):
            m=mel[((bi-1)*2+k)%len(mel)]
            piano(m, t+k*2*beat+0.02, 2*beat, 0.22, 0.25)
    t+=bar; bi+=1
# final Am chord
piano(45,DUR-3.4,3,0.3); 
for m in [69,72,76]: piano(m,DUR-3.4,3,0.15,0.1)
# reverb: multitap delays
rev=np.zeros_like(out)
for d,g in [(0.031,.5),(0.047,.45),(0.073,.4),(0.113,.35),(0.167,.3),(0.241,.25),(0.353,.2),(0.509,.15),(0.701,.1)]:
    k=int(d*SR); rev[k:,0]+=out[:-k,1]*g; rev[k:,1]+=out[:-k,0]*g
mix=out+0.45*rev
# soft vinyl-ish noise bed
mix+=rng.normal(0,0.0015,mix.shape)
# fade in/out
fi=int(0.25*SR); fo=int(2.5*SR)
mix[:fi]*=np.linspace(0,1,fi)[:,None]; mix[-fo:]*=np.linspace(1,0,fo)[:,None]**1.5
mix/=np.max(np.abs(mix))*1.12
pcm=(mix*32767).astype(np.int16)
with wave.open(sys.argv[1],'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
