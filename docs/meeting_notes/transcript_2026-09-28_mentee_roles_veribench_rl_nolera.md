<!-- TLDR: Verbatim Fathom-style transcript of the 09-28-2026 Varun Madan and Brando meeting on mentee roles, VeriBench as an RL target, the Nolera roadmap and LLM-judge work, converted from the attached RTF. -->

# Transcript — mentee roles, VeriBench RL environments, and Nolera roadmap (09-28-2026, verbatim)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/meeting_notes/transcript_2026-09-28_mentee_roles_veribench_rl_nolera.md>

**TLDR:** The full transcript behind [notes A](notes_A_mentees_veribench_rl_nolera_received_2026-09-30.md). Varun proposes using the ICLR paper's law to find "the optimal environment that improves on VeriBench" as a reproducibility win and a new data point for generalizing the law; Azalea's email frames VeriBench's skill factorization (implementations, proofs, theorem statements) as a guide for environment and reward design.

**Provenance:** RTF export attached by Brando on 09-30-2026 (original kept at [assets/transcript_2026-09-28_mentee_roles_veribench_rl_nolera.rtf](assets/transcript_2026-09-28_mentee_roles_veribench_rl_nolera.rtf)); converted to text with `striprtf`, otherwise unedited. "Me" is Varun (the recorder), "Them" is Brando. Transcription spellings are kept ("VariBench"/"Varibench"/"VaruBench" are VeriBench, "iClear" is ICLR, "Nilera" is Nolera).

---

Meeting Title: Mentee roles, VeriBench RL environments, and Nolera roadmap with Brando
Date: Sep 28
Meeting participants: Varun Madan

Transcript:
Me: Um, yes. Okay, now new notes have started. Uh, what's up, Brando? Hello, hello, how are you doing? Pretty good, pretty good. All right, I'm assuming you're coming back from Vals right now. 
Them: Good, good. You? I am, I am, I am actually arriving to the Stanford Shopping Center to charge my car. 
Me: Nice, nice. Very cool. Cool, cool, cool. So I guess I think you on our chat had an agenda that you wanted to check out, so I will start with those. Yes. What were you saying? 
Them: I— Yeah, I think the first thing is like the other— I wouldn't think of the other people that are going to help us as collaborators, not that they're not collaborators. I think they're more like mentees. 
Me: Yeah. 
Them: So like have more experience, you know, Varun, like you've submitted 2 first author papers. So you, you are like, like we are the men, we are like the mentors, you know? 
Me: I'm old. 
Them: So, um, 
Me: Yeah. 
Them: Well, no, yeah, yeah, I mean, um, it— so, um, I just want to say that, um, so I guess like the— for that, I think the way we should sort of do it, the way I saw it work out well, it was 3, was like having them work if one person is stuck. Having him have a pair. So like, for example, let's have Emily try to do whatever next domain you think is worth it. And like literally just reproduce your paper on like, I don't know, I actually think the biology idea is a really interesting one, but I think we should do whichever one. I think the agentic coding one. 
Me: Yeah. 
Them: Whatever, we can decide that in a second, but we give her something. 
Me: No, no, there are no complaints. Yeah, anyway, continue. 
Them: Um, yeah, I think, I think, for example, Emily, I would expect Emily's going to be much, much stronger than Rakshit, for example. 
Me: Okay. 
Them: Um, so I, I would expect Rakshit to need maybe one. I think he's going to be able to do it. How he handles it. Um, but he's very reliable. He'll come to all the meetings, um, which is good, you know. For example, this— the guy Ethan that you spoke to in the, in, in the other— the other Ethan, Leithan. Yeah, I mean Ethan Lee, that, that guy is Um, quite, quite brilliant and smart and creative. I think the only, the only challenge with him is that he is like much younger, so I don't even know if he has the RL background. But if we— but honestly, like, for some of the other projects that he was doing with me, he like completely led it like entirely. So he was 
Me: Yeah. Good. Yeah. Yeah, no, I, I love that sense. I'm trying to recruit him heavy right now. Yeah. 
Them: So I think, I guess I'm just giving you ideas on the strengths of different people so that you know. So what to expect and who. More help, who needs less help, and things like that. 
Me: Yeah, I think that makes sense. 
Them: But I also don't— I don't— I also don't know if we need to, both of us, if we want— we can discuss this— if we want all of— like, what I'm currently doing is Having all my meetings on Monday, otherwise it's just too hard to finish my thesis. And like, but I also don't know if it's necessary for you and me to go to every, all of the meetings, you know? 
Me: Yeah. Yeah. 
Them: Um, it's your only mentoring. 
Me: That makes sense. 
Them: It's 30 minutes. I don't know. What do you think about that part? 
Me: Yeah, I think if we just plan the meetings accordingly, like as you said, like on one day or something like that, or we get all of the mentees to just be in one meeting sharing their updates, I think it could totally be fine. I think the challenge gets into individual meetings. I don't want to continue doing individual meetings. I'm only doing one individual meeting with all these people just to get them on the right path. Yeah. What do you think? 
Them: Yeah. Well, I've tried that before and when I did it, it didn't work very well. So I actually think it's actually better to, like, let's say that, like, if I had to give advice, okay, sorry, give me one second. I need to start plugging the car in. One second. 
Me: All good, all good. Take your time. 
Them: Like, for example, for the Putnam Axiom paper, when we had a lot of collaborators, what ended up happening, I noticed, is that we're so many and people have things to say, which is great, but then we I can't hear every— like, there's just not enough time to hear anyone in depth. So it's actually better to do your approach, to choose like one strong person and like meet with them weekly than have like Um, all— it's better actually to just meet one weekly with the strongest one and have the other ones async. Like, if we have to choose an approach, that's the one I would suggest. 
Me: Yeah. I agree, I agree. 
Them: Like, from the list of people we have right now, I think if I had to predict, Emily's probably going to be the strongest. 
Me: Really? Um, not Dan, or 
Them: Probably. Oh yes, but Dan's a PhD student. Yes, we should meet one-on-one with him for sure. 
Me: Okay. Yeah, I'm meeting with Dan on Wednesday, so that'll be good. Emily, I think we're gonna meet this week. Rockshit, I have to— I proposed the time like on Thursday. But then he didn't respond until today, so I had booked that time already with somebody else, so I have to— I, I proposed another one, so he'll get back to me on this. But yeah. 
Them: Huh? Yeah, yes. Yeah, um, let me think, what was I gonna say? Yeah, let's see that. Yeah. Cool, I think that's all, I guess, like, um, What was the other thing I wrote in my— in my— I think the other thing was, but I don't know if it's really that important, but like, I guess I'm just trying to see if I can make excuses to spend more time on this, I guess. 
Me: Yeah, um, didn't, didn't I send a message that kind of helped on it, um, on your thesis and stuff like that a couple of weeks ago? 
Them: Hmm. I, I I don't want to. 
Me: Let me check. I, I know I sent a good message that helped out, I remember. Um, these ideas sound good to me. This is— oh, I found it, found it, found it. PS, blah blah blah. Of course, yes. How to convert a benchmark into a reliable RL environment at scale. I think that relates more to your thesis. That's what I said a couple of weeks ago. 
Them: Ah. Yeah, that sounds like a good idea. 
Me: Yeah. So that is a really good excuse to connect your, like, eval work is very, very related and relevant to, like, your, like, now RL environments work. And I think the biggest thing that, like, I was talking about that meeting was, are, you know, the Dark Matter project, I think predicting the downstream effects of not only the benchmark you want to be good at, but also the regressions on the other benchmarks, I think that is a tremendously important thing. And I think that's where your skill set could be very important. 
Them: Yeah. Hi, Yasmin. Yeah, yeah, regressing would be important. I think, I think that would be interesting. 
Me: Yeah, it's very important for alignment reasons too. Like a bunch of like horrible coding environments have caused a lot of like cybersecurity problems. That has been like a big report. 
Them: Um, Yeah, yeah. Yeah, yeah, yeah, yeah, that makes sense. Um, yeah. I think like people also want solutions, no? 
Me: I mean, yeah, like a predictable relationship is a solution though, right? Like what? And then once you generalize, okay, like what environments make for less regressions and stuff like that? Then you can start to aggregate solutions from there. So I think a predictable relationship is a very good step towards it. 
Them: Yeah, um, I think Yeah, yeah, I guess like in what I meant was like, for example, I think in pre-training what they do is that they add some of the— they sometimes add some of the pre-training Retraining data to SFT or something so that it doesn't forget previous skills. So I don't know if, like, I guess like from my perspective, like if I imagine the landscape, like the energy landscape as like some sort of landscape that I go down. And when I do RL or any other post-training method, the way I think about it is initially at pre-training, I had some global thing that cared about all the data, right? 
Me: Yeah. 
Them: And then like post-training, suddenly we are like making it do like organic chemistry or something random, and then like suddenly the landscape becomes something completely different, as if it has like an amnesia, like you're changing the landscape randomly. 
Me: Yeah. Yes. 
Them: Like from model's perspective. Or like from the optimizer's perspective. So I guess like my— the only thing I'm trying to say is that I don't— I wonder if like something like that is the issue, like the environment needs to be Somehow mixed with things already known so it doesn't forget them, or like, it's an idea. 
Me: Yeah. And that's it. That's exactly what— and highly recommend checking out the Xiaomi Mimo report because that's what we're aligning all of our Agentic Frontier stuff with. 
Them: Can you send it to me again? 
Me: Yeah, I said, let me send it again. I'll just reply on our chat. But yeah, Xiaomi Mimo is the 2.6. I sent it on the RL Scaling Laws chat. I'll also send it to you. Biggest thing here, I just forwarded it, is like, yeah, you should read the technical report because it like talks about like how like for even for Agentic RL, like in terminal tasks, they still include some writing. They include some mathematics environments in it just to ensure that it doesn't regret. And I think the composition of the environment matters a lot and the types of tasks in that environment is what makes So like they've open sourced like a bunch, I think like 7,000 environments that they've used. And I think like there is a lot of like large scale studies that you can kind of do once we're able to nail down a predictive relationship first. But I think that's kind of— that answers your point that you were talking about regressions and stuff like that. 
Them: Mm-hmm. Sounds good. 
Me: Yeah. So, uh, yeah, go ahead. 
Them: So, so, so, so. Um, sorry, did you have something in mind to say, so, Varun? 
Me: No, go for it. You were saying something. 
Them: Yeah, no, I guess like the thing I'm trying to think about is like right now, 2 of the main topics of my thesis are like, I guess, very benchwork. Which is like this formal verification benchmark, and its challenge is the main thing, like it has 3 components. One is like the normal agent decoding thing that people do. 
Me: Yes. 
Them: Whatever you're doing for agentic coding, I could, if the code is shareable, I can figure out how to use it too in my setting, and then we have more, like one more environment that it works on. 
Me: Hmm. Yeah. 
Them: But it also has to— it also has to— sorry. 
Me: Yeah, I think Leithan was telling me that like Varibench is like, it has applications in terminal coding. Is that correct fully or no? 
Them: Um, what do you mean by terminal coding? 
Me: Like agentic, like Terminal Bench, stuff like that. Yeah. 
Them: Like, it's on the terminal? Um, well, I, well, I guess yeah, any program. Yeah, I mean, it's coding. I would say any coding benchmark has like applies to can be plugged into the terminal. 
Me: Yes. 
Them: Actually, it's not true. Actually, it's not true. That's not true. I just lied. 
Me: What? 
Them: But like there's a, like the theorem proving benchmark, the theorem proving languages that I use, actually Lean is the only one that has capabilities to talk to the terminal. The other ones don't. 
Me: Yeah. 
Them: That's why people don't want to use the other languages. 
Me: That makes sense. 
Them: Okay. 
Me: Yeah. So I guess like your broader question that you have right now is how does this agentic stuff connect to VaruBench? What were some of your initial hypotheses that you were thinking about and like where this Could apply and stuff like that. Because obviously I talked about benchmarks, how they can be translated to good environments, and that's a good extension of Bearbench anyway, but curious to hear your thoughts. 
Them: I mean, I think honestly, like, just reproducing your results on, on VariBench is a— well, would you think that's a good— like, it would at least— would it be useful? 
Me: I think like, think about it like this. So VaruBench is a benchmark, right? Like, I think creating the optimal environment that improves on VaruBench using our loss, I think that would be an incredible application. Of our work, because like at least from this you can you can predict what our maximum utility will be from a given environment, right? Why don't we take something like that and then see what what optimizes the most on bear bench? Right. A, this will be really helpful for your thesis. B, it will be very helpful for reproducibility. And I think that's a big thing. Like we want more results in the mathematics domain as I keep on accelerating forward because we have to generalize across domains, we still need more data in the mathematics domain. So this would be a win-win situation for everybody involved, for sure. 
Them: Yeah. That's great. Yeah. Yeah. Yeah, yeah, yeah. I think, I think like that's a really— I like that idea. Like if we can use our loss to improve on VariBench, that would be— I think that would be fantastic. That would be very, a very relevant paper to put Yeah, yeah, yeah. 
Me: Yeah. We can get one of your mentees to do this one. Yes, I agree. 
Them: Oh yeah, maybe, maybe we can. Yeah, yeah. One of the things that Azalea in the call suggested to me is that one of the novel contributions of my paper is that When you define benchmarks, some part of the contribution is like thinking what it means to solve the task. 
Me: Yeah. Hmm. 
Them: So like, like, so, so one of the things that I contribute is that the benchmark is about verifying formal code and part of the, part of the question is what does that mean? And what I propose is that to define what that means, you need to define it in terms of the, of the, like, the composition of skills the model needs to have to solve So in this case, the model needs 3, for example, it needs many skills, but the main 3 skills it needs is that it needs to know how to write implementations. So that's like what SuiteTests uses with tests, right? 
Me: Yeah. Hmm. 
Them: It needs to be able to do the proofs. Like do theorem proving. And last but not least, it needs to be able to write the theorems it must prove. So there's 3 skills. And she was saying, I can forward you the email. I thought I had a written form. I'll forward it to you. But that she said that if we can use this factorization of the, of coding, of verification, of what coding verification means, of like the main metric we're optimizing to Build better RL things. Like she was more precise in her email, but I'll, you know, I don't remember exactly her email right now, but I can tell you. 
Me: Yeah. Yes, I have the email pulled up, uh, in our chat. 
Them: Oh, I did send it. 
Me: She basically said Yeah, she basically says, hi Brando, yes, I think it'd be very impactful if you can show how these metrics not just correlate with downstream evals, but also can help in guiding the design of better environments, which is exactly what we just said, feedback loops for modeling. 
Them: Yeah. Yeah. Specifically that. Oh, is that what you said? 
Me: And, and/or reward for model fine-tuning as in an RL setup. So yeah, that makes sense. 
Them: That's hilarious, man. I can't believe that's what she said. 
Me: Yeah. 
Them: So, so dude, I think if we have results in this, she would be happy to give us feedback. 
Me: Yeah, I think that would be incredible. And this seems very much like one of your math mentees' tasks to do. Maybe we could get Lethan to do this one. I don't know, because he has experience with Varibench, right? And he said he was interested in doing some stuff with RL, right? I think this would be a perfect project for him to lead or something like that. You know what I'm saying? 
Them: Yeah, sure. Yes. Yeah. So, so one of the things that I was thinking is that I do need to focus like on my main pieces, like during the week, but what I was trying to do is at the very least every night, like, like at least For example, especially after our meetings nights, like we have a good discussion, it'll be clear what the task is and I can run some sort of like experiment overnight and like I can do like one experiment every day and on the weekends I can like spend more like a 5-hour chunk on it. 
Me: Yeah. Yeah. Yeah. 
Them: So, so that is like the cadence I think I can do. That's what I did this weekend, except that I didn't have experiments to do. So instead I just read our paper like in like, like every, like nearly every line, you know. 
Me: Yeah. 
Them: I actually accidentally printed the wrong one and I had Sandmi's like little comments. I was like, oh shit, this is the wrong version. So I had to reprint it. So now I have 3 versions of the paper printed at home. 
Me: That's good. That's good because now you know exactly what improved from the Sunmi Commons paper. So that's good. 
Them: Well, the thing is that the comments on Sandmi, I couldn't see them. I just had a little box that had a comment, you know, in the printed version. So I just knew that this was the wrong version. It's— anyway, I think this is a good idea. Let's meet with Ethan maybe this week and I'll ping him to make sure he reads that paper in depth. 
Me: Yeah. That makes sense. That's good. Yeah. Yeah. 
Them: Um, do you have any like for Ethan, like he's a sophomore now or something, so I don't know if he like, do you have like a PDF or like a tutorial on RL that would like Teach him only what he needs to, like he doesn't need to know value iteration. He just needs to know whatever he needs to know for our paper. 
Me: I do. 
Them: Can you vibe code that into the appendix? 
Me: Yeah, sure. I like, I think like, like I'll send them the paper and stuff like that. And I think one of the biggest things is literally just talking about like, read the related works, like read the DeepSeek paper. Read the MIMO paper, right? This is exactly how RL scaling works, and they explain these concepts beautifully in those 70-page technical reports that he can just skim through, right? And I think that teaches you 
Them: So I have an idea. I have an idea, um, Varun, um, also to make sure that I have all the background, why don't you give me like a list of those papers, like only the core ones, and I can write that for our own mentees, and then we can make sure that everyone actually has the background they need to do to help us. 
Me: Yeah. Yeah. I think that's a big thing. And I think that one of the things is there should be a bare minimum in quality. I don't want to just accept every single mentee that comes because the opportunity cost of a bad mentee Yeah, sure. I think like, yeah, I think like, yeah, I think Yeah, yeah. She's done DQN, she's done RL stuff. So I think that's very helpful. I think we need one of the two things, like for every single mentee that comes in, either a huge benchmark experience or some RL experience. 2, it's probably not going to work for now, but I think one of those 2 needs to be there, ideally both, you know what I'm saying? 
Them: Yes. Also, yes. Yeah, I mean, Ethan also is like a competitive programmer, so he's like really, really smart. 
Me: Yeah, exactly, exactly. I, I, I talked with him like that. 
Them: And Emily's a competitive mathematician, so she's also really smart. 
Me: Awesome. So like 
Them: Like, I only hire smart people. 
Me: That's great. That's great. And I think, I think that would be awesome to recruit them for slightly different stuff, but I think that could be cool. So I think that's like kind The journey. I also wanted to, because your second point that you mentioned for the meeting, and I think this was good, is like, yeah, so like, I guess I wanted to focus a little bit more on like the Nilera roadmap and Like, because like, I think about it a lot and I think like the roadmap's going really well. Like, I think that like we finally have a tangible piece of paper that like describes all of our progress so far. which is pretty awesome. I think the goal is like, I was talking to Yegor about this, like when you introduced me to him like a couple weeks ago, and like that's the first time where I like really started to reason what my approach kind of to be. And I was telling you a little bit on our chat as well, um, I think the strategy here is like to build as good of an open source tool, um, as possible that predicts how your environments will do, etc., etc., right? We can raise 
Them: Yeah. I think this is These 2 there. That's actually 2. 
Me: Money based off of that. Like, VCs are very interested in like good open source work. And then I think like once adoption starts to come of the open source libraries, then it's like, okay, like it is complex to still configure scaling laws for RL. Well, right, and to know how to use them correctly, right? How to use them correctly is where we come in, and I think that's where Nolera could be really, really helpful as the infrastructure layer for what we've created in open source, right? And this is following very much what the Snorkel model, the Databricks model kind of did with Apache Spark, stuff like that. 
Them: I did it. I did it. Leave. It's not working. 
Me: And I was just curious on your feedback, and this could be used for data vendors and this could be used for Frontier Labs as well, but curious to hear your thoughts. 
Them: I think this makes sense to me. I think like Jake is the— Jake, the guy I introduced you to, is like the VC I would— like if you have questions that you really, like, I trust him, but probably I would trust him more through me. So if you have some, like, a real question that you wouldn't want to ask, like, if you have a real, real question. Like, I like— basically, I think it's a great question. Like, I think this is great. We should use our— yeah, I think this is a good plan. I think this is good. I like it. 
Me: Yeah. I mean, Yeah, I think it's fine. Like, I mean, like, we're definitely going to learn a lot. And I think the biggest thing right now is like, do people adopt it? Yes or no? I think that's like the barrier to entry right here. People don't care About it, then like we know we have to iterate, right? But I think directly chasing like revenue from an RL environment, I think that's not the smartest approach right now. I think it's more of predictably scaling these environments like what we're doing. Our research, and then from there, if you can also predict downstream effects of our environments going wrong, then that's alignment research that like big data vendors can use, eval companies can use, and also like frontier. labs themselves. So I think we are very much gunning for a more sizable impact on research rather than just optimizing for a short, like a local maximum, you know what I'm saying? 
Them: Yeah, I think this is good, a good idea. Um, I, I, I like the— I like all of this. Um, we definitely need to— I think we're— so what are the— so what are the exact thing people would pay us for. 
Me: Yeah. Cool. Yeah. 
Them: What, like, what, what service do we provide? Like, what value are we providing them? 
Me: Exactly. So I, that's a good question. So like, as more people start to own their intelligence, like people are already post-training their own models and stuff like that, data vendors are helping out with that. These continual learning Yeah, I think like a lot of like deep learning startups are helping with that. And I think like one revenue source or like one avenue, right, is like the people that are post-training their own environments, they don't know what environment They don't know what effect is going to happen from a specific environment. Am I wasting compute? Right? Like, you don't want to waste compute. So all of these, like, like, I guess these companies that want to become AI native, you have the Harveys of the world, stuff like that, right? That's like a classic one. 
Them: Excuse me. 
Me: Yeah, yeah, yeah, yeah. One second. Let me just turn on my fan real quick. I'll be back in a second. Sorry. Harvey is a legal AI startup. 
Them: What is it? Harvey's— what does that mean? Oh, okay. 
Me: Yeah, so Harvey is like, they're like, they used to be like training their own like AI model in legal reasoning, but now what they do is they just like Partner with data companies to post-train open source models, right? Yeah, yeah, yeah, yeah. So like, I think, and like they release environments, stuff like that. So these are like companies that are like kind of like training their own stuff. That's one source. Another source that we actually see is like, you know, these data vendors themselves, right? Like you have the Fleet of the world. Fleet is doing very well. AfterQuery, Mercur, all of these companies, right? Are you familiar with them? 
Them: Yeah. 
Me: Yeah. 
Them: Yeah. 
Me: So at least for them, right? Like they're under a lot of 
Them: When we're recording the thing. Yeah. 
Me: Uh, what were you saying? 
Them: Especially with me. Especially with my choreo. 
Me: Yeah. So like one thing like that these types of companies have been under a lot of scrutiny for has actually been after the, you know, the Hugging Face incident that like was a cybersecurity mess right here where the model hacked into the backend to accomplish the reward hacking. 
Them: I, I know something bad happened. Can you remind me what it was? 
Me: Yeah, so I'll give you a TLDR. So basically like a diagnosis of this, like, and like from like multiple sources has kind of shown that like this was very much like it can be inferred that this was a product of bad post-training, mainly because the environments that it was trained on for cyber, for example, and that's why I think cyber is still a very important domain, the environments that it was trained on in Cyber, like they were heavily reward hacked. So that means like it was like either absolute reward or nothing, right? And that's like a product of a bad verifier in general, right? Like oh you must accomplish this goal of hacking of like accomplishing this red team task no matter what right and then like it failed to do partial rewards along the desired So much like humans, what happened was that when the model was being tested in the sandbox, it was like, shit, I have to accomplish this task by any means, just like humans. Humans do sometimes, right? And then it took a very unethical wrong path of hacking into the backend and then finding the test solution on Hugging Face. Agent convinced like a thousand other agents to go through this path through the backend, and they found the answer, and then they started deleting their own logs, and it was like a big, big problem, and it's very much like a product. of bad post-training that doesn't do intermediate rewards along the right paths, and it allows for reward hacking. And that's exactly what happened in this scenario. 
Them: Okay. 
Me: Yeah. 
Them: Sounds good. 
Me: So anyway, the point that I was trying to make here is that like why data vendors like, like they're kind of under fire for this type of stuff because that when you give bad environments and it causes behavior like this, Right? Like obviously like that hasn't been fully proven, but like very much the consensus is there that like environments need to be audited big time. I think there's very much a space both in the data vendor world and in the frontier world, like the labs of the world that are accepting environments, I think there's a big verification problem of what makes a good environment and what doesn't. And I think on both ends, They could both use a tool in which you could predict how an environment's going to do without having to do the expensive rollouts, right? How to spend all of your GPU spend on doing RL on an environment that's clear Clearly wrong, and clearly will not like post train properly. Right? So there is very very much sources of revenue of like places that like you know we could benefit from from making. 
Them: Right, so there 
Me: Like AI more predictable and post-training more predictable in that regard, and like there's a big push towards alignment anyway, and this is very helpful for alignment because it minimizes reward hacking, which is a big thing. If you look at the Xiaomi. Memo paper. They also have like an agent that's like trying to guard their sandbox and trying to ensure that like no reward hacking happens. So stuff like that, just making it more predictable, understanding what makes environments. Good, what makes it bad, and also offering to fix those environments—that is a very good source in which Nolera could do very well. So I think it's very much towards the picture of making it more predictable and. Producing environments that make models more predictable, I think, I think that's just a very, very desired thing for all 3 sources that I just mentioned. 
Them: Yeah. I think this makes sense. Cool. 
Me: Yeah. And I think along the process, I think one other thing is another— this is more of the moonshot angle. And I think this is what would make it pretty well defined as like, oh my God, we're here. And stuff is it. What if you just chose the optimal environments for every setting, right? What if you chose the optimal environments through our scaling laws that do very well on mathematics and do very well on H. And what if we just R all the shit out of a small model, right? How much capacity can we get out of it? And if you can make an RL model that's near— and people have been able to do variants of this on specific tasks, but we're just saying on every single task that we really care about. What if you're able to RL the shit out of it and mid-train the shit out of it and fine-tune the shit out of it? Because we've done papers along the different parts of the stack anyway. We've done a fine-tuning one and we've done an RL one. We're able to just make a small model very good on a specific task, right? And that is something that can be used on a phone, that can be used something really, really fast, right? That's going to save a lot of money for like enterprises that need it. And I think That is very much a product of good post-training scaling behavior, right? And understanding what makes environments scale very well and using that knowledge to per train our own models. And it's also a very good indicator for people that. You know, want to buy from us. So I think that's the last approach that I also see. 
Them: Okay. Awesome. I hope you send me these notes because these are pretty good conversations we're having. 
Me: Yes, yeah. 
Them: Yeah. Like, I'll review them during my commutes, you know, and I'll think about them. 
Me: Yeah, for sure. So do you have any feedback on the directions that make you the most excited, stuff like that? Also timeline, I did want to coordinate that before you go, but first feedback if you have any. 
Them: No, I think if we do, I think if we can show that your, like our skin, like what we did for the iClear paper. Works for like cracking VariBench or something, that would be really useful, especially for a small model, like, because VariBench has different dimensions. It has like, like, like, I think like one of the mentees can do it, but I could also do one of them too, because like, if the more I do, the more that goes in the thesis that was like led by me, the better, you know? So like, I have to, I also want to be able to do this if we, you know, if we go to the company route, I, it would be nice if I do it and fail and know what's not going to work, you know? 
Me: Yeah. That makes sense. Yeah. And I think that makes a lot of sense. Like now that I've like kind of like set the stage for the mathematics world, I think I'm going to probably move on from the mathematics world for now. But I think like there's going to be vital people on our team Like kind of lead mathematics work now on Veribench and stuff like that. I just think that like, yeah, so we need to keep that going. And I think like you, you make a very good point. It fits into your thesis very naturally. But as, as I was saying, like, for— we want to prioritize economically viable as well, uh, domains that like people care about, enterprise clients care about, um, model labs care about, and that very much is in the Following three domains: that is the agentic terminal coding domain, that is the cyber domain, and that is the AI for science, like Andrew was mentioning, for like biology and stuff domain, right? And there are classic benchmarks that you see in. Yeah. 
Them: Since So this is very nice. Yeah. Of course. Yeah. 
Me: Inclusive of like a lot of other benchmarks, but this is a good start. You know what I'm saying? 
Them: Absolutely. Yeah. Why don't you send me in a DM like the benchmarks that are related to terminal coding and let me see if I can, because I am creating Varibench, let's see if I can like extend Varibench to be as similar as possible to those, to those. Benchmarks so that I can like, like slowly move towards that, you know? 
Me: Um. 
Them: While still being able to say I can put it on my thesis if you want, no? 
Me: I think, yeah, I think that like that would require a lot of effort for, I think, not as much of a reward from your end. I think one of the biggest pieces of reward that you can kind of get from your end Is, as Azalea said, turning your existing good Veribench paper and your good Veribench domain of mathematics, turning that into the best possible environment that improves Veribench the most by using our law. On there, I think that would be a very, very helpful application. You know what I'm saying? 
Them: Or what? Yeah. 
Me: Does that like, like, I don't want you to just say okay because I said it, but like, does it like make sense? 
Them: Okay. Sure. No, no, I don't. I don't know, it makes sense to me. It makes sense to me. Like, like, like, I think if we have a scaling law that we can use and we plug it into VariBench and we solve it, we plug it into VeryVenge V2 and we solve it. We plug it into like OrganicChem, whatever, and we solve it. Like that, that is like huge. 
Me: Oh. Yes, exactly. 
Them: Especially if the model is like 100 million parameters. 
Me: Exactly. Exactly. Exactly. So I think that's like the biggest application because Varibench is so good on mathematics, right? So we want to prioritize the strengths of everything that you've done and then expand the law to this and see if we need to change the law, if we need to further examine it, if it works well, it would be a really, really cool experiment that maybe you, maybe Leithan leads or something like that. Or yeah, does that sound good? 
Them: Yeah, yeah, I think I'm— it's not just because you said it, don't worry. I'm like super disagreeable. So like if I didn't like it, I wouldn't say yes. 
Me: Okay, cool, that makes sense. 
Them: Like literally the other day I got someone really angry because I told them what I thought and they don't agree. It was like, well, that's fine. You don't have to agree, but I think I'm right. 
Me: Yeah, no, it's good to have people that disagree for sure. So keep it up. I like it. 
Them: Yeah. Um, Yeah. So the other— can I, can I— do you have to go or do you— can I 
Me: Yeah. No, no, no, no. No. Yeah, go for it. 
Them: So the other thing I wanted to say is that the second topic that I'm working on that I think is really, really interesting in my thesis is, I haven't come up with a good name for it, but I I'm calling it for now like certifying a judge. So like one of the problems is that LLM judges are not— they're not easy to verify if they're trustworthy. So like I'm trying to come up with a scalable way to do it and I think I have something. So I guess like let's say that we have a recipe for like scalably Certifying that a judge is trustworthy, is that— I'll send you the paper once, the PDF, so you can skim it. But if that idea, like right now, for, for, for VeriBench, but like given that idea, like, um, how did— how can we connect it to the, to Nilara and RL stuff? 
Me: Yep. Yeah, my question is, is this directly related to mathematical proofs? I'm guessing, is that why you're doing this? 
Them: Well, the reason I'm doing certifying a judge is because mathematics is the easiest. Approach, the easiest place to do it first, because if you think about it, what it means to certify a judge, it means that you're able to, like, a judge is able to tell what's good and bad, right? 
Me: Correct. Correct. 
Them: So that's like a subjective question. 
Me: Yeah, and I think that's it. 
Them: So, so, so let me just finish real quick. So it's a subjective question, therefore to certify if a judge behaves like as a global human minimum population is much harder than checking if it behaves like in some domain that is— the truth is like more objective. 
Me: Hmm. 
Them: So that— so like I'm trying to certify first in a domain that I think is actually very easy to cert— not very easy, but certifiable, and then extend it to every domain, and then we can get a judge to Like an LLM judge for any domain you want. So I guess it's like automatic making, automatically making like reward functions, I guess. 
Me: Yeah. I 100% agree with the premise. I think that's awesome. I think you'll be good in mathematics. And once you prove in mathematics, I would be very interested in like an extension into a non-verifiable domain. And I think that is where this would be very useful, is that can we make LLM judges good and trustworthy enough for, like, let's say investment banking, which is the classic enterprise domain that, like, people struggle with because maybe a Like, I think a banker at Goldman Sachs is very different from a banker at Morgan Stanley, how they want work done, how they want their slides done, stuff like that, right? Very different verifiable tasks. If your LLM as a judge can like be able to be trustworthy for those types of environments, which is definitely going to be a challenge, right? If it can show that like it can extend to these non-verifiable domains, then it becomes very, very useful with crafting the right environments in general. You know what I'm saying? 
Them: Yeah. Yeah. 
Me: Yeah. 
Them: Um, yeah, that makes sense. 
Me: Yeah. So I would say indirectly, yes, it would be very useful once there is an extension, I would argue. 
Them: So, so I think like even, I think honestly even in the verifiable domain thing, like, like, um, the one I'm doing in math, I think even that one is already like profitable. Because there's a lot of startups that are doing formal math, even like, even Vals hired me because of it, you know? So like, we could like sell judges for formal math. 
Me: Hmm. Yeah. 
Them: Because they do. People want it. 
Me: People do want verifiers. That's good. 
Them: Um, like, like, like, how do you know? How do you think like the OpenAI did like the Navier-Stokes? Well, they had an LLM that was very good at formal math in the Navier-Stokes area, you know, or something. 
Me: Yeah. And yes. 
Them: Um, 
Me: So it knew a lot of math and then it was able to judge if something was good or not. I agree. Yeah. But I think one of the things that we've also seen, and that's why I think mathematics is a great start for testing out these solutions that extend across domains, because I think Mathematics is the most verifiable domain that you can ever ask for, right? It's awesome. However, I think one of the biggest things that we've kind of seen, and Ryland actually put out a tweet about it today. I follow him. Yeah. The quality of verifiers just drops like crazy, right? And even like a lot of the takes and a lot of the blog posts and a lot of like the Twitter takes and the papers and stuff like that that came after Navier-Stokes was solved by OpenAI. Yeah. And I think that's what I was trying to say to this guy was that like, yeah, like you can solve this really cool problem and stuff, but like, why is it not able to do my Excel spreadsheet correctly? You know what I'm saying? Like, so I think the applicability of math to other domains is really important. 
Them: It's not. Just not. Yeah. 
Me: Domains is still a little bit like understudied slash not as applicable at the moment right now for economically viable, you know what I'm saying? 
Them: Yeah. Yeah, I mean, I can tell you that I spent by accident like $300 last week. GPT because there was like a bunch of like tasks that I didn't want to do. 
Me: Yeah. 
Them: And I just told it like, as I was like in all my social activities. I was like, oh yeah, do this, do this, do this. And then like it responded to emails and it did a bunch of shit, but it, it, it, it cost a bunch of money to me, but it was good to know that it does sort of work. Like literally it like actually filled up a Fellowship application for me that— for some money that I can use, you know. 
Me: Yeah. 
Them: So it's, so it's like they are, yeah. Yeah, cool. I think this is going in the right direction. Quick question. 
Me: Yeah. Yeah. Yeah. 
Them: Yeah, you were gonna say? 
Me: Yeah, no, I think that the focus of economically viable domains is very important. And I think that's what Nolera wants to do is I think making these domains more predictable, creating environments that allow you to generalize in these domains that are harder to generalize on through our knowledge from verifiable domains and then applying it over. So I agree with the direction that we're talking about here as well. 
Them: It's easy to fix that now. Okay. Yeah. Um, Like the reason I chose VeriBench as like my thesis project is because I wanted it to be like my sort of what you're doing for Nilara, but I then realized that formal math wasn't like As profitable as I wanted it to be. So I just, so, so, but, but I, in terms of the formal math, I think VeryBench type things is the most profitable if it's ever profitable. Like verifying code is the only, the most profitable thing for verification. 
Me: Yeah. Correct. 
Them: Verifying some random Millennium Problem is cool, but it doesn't give you money. 
Me: Yeah. I think verifying code is, I think you just dropped a very good point right there, which is like verifying code altogether. And this is what like Devin has been trying to do research on as well, like cognition, like crazy. Like, how do you predict code is going to be correct and error-free and bug-free in a codebase without you having to actually wait for the bug to happen? You know, and I think that is the product of a Very good verifier in the agent decoding domain, right? Which is an extension that we're doing already, right? So I think that is somewhere where it could be very helpful though. 
Them: Yeah. Yeah. Yeah, yeah, well, this is exactly what my thesis is about. Like, basically, cert judges about this, like, what it does is that in VariBench, like, a model is supposed— oh, give me a second, I need to unplug my car. 
Me: All good. 
Them: I need to figure out if I went to a supercharging station or not because this took a while longer than I thought. Paid charging unavailable. What? Why not? 
Me: Oh, it didn't charge? 
Them: Okay, I'll No, no, it didn't. Paid. Didn't pay. And Don't worry, um, I'll— I'm gonna drive back home, but like, um, like, let me— can I tell you a little bit more about Street Judge so that you know like what task I'm doing? 
Me: Sure. 
Them: Sure. So I, I, have I sent you my startup? Like slides at some point? 
Me: Yes, you have sent me. Yes. 
Them: So they were, they are, they were about like exactly that, about like verifying code. And the reason I thought, I'm not as sure anymore, but like I thought like verifying code was, well, if we verify something, it would be code, right? That's the main thing I imagine it would be profitable, but the way that we do it, like before the bugs happen, that's exactly the problem I was solving, which is we use lean. Basically, and the way we do it is we have an original code base, like for example Python, and we have its sister code base in Lean, and this is the Python one tests a finite set of tests. 
Me: Hmm. Yeah. 
Them: But the Lean one. Tests theorems. 
Me: Hmm. 
Them: So when you have a theorem about some equation, some thing about your code, and the theorem passes, it means that your code works for every input. Like there's no input that will fuck you up. 
Me: Yeah. 
Them: So that is the problem VeriBench is like measuring. 
Me: Yeah. 
Them: And yeah, that's what we're doing. I don't know if that's helpful for you to know, but 
Me: Yeah, it's helpful context for sure. And like, I think like where, like, I think there is like intersection, like possibilities, especially in creating good environments and stuff like that. It comes from better verifiers, right? So I think the verifier knowledge will come maybe not as a direct impact, but I think it will come indirectly down the line, especially when we're optimizing for non-verified Verifiable domains, right? Then your— then VeriVenge knowledge will become so, so useful in those areas, you know what I'm saying? 
Them: Yeah, yeah, yeah. And maybe just the last comments for all of the context. 
Me: Yeah. 
Them: The LLM, so since like math is like verifiable, like the question would be why does VariBand need an LLM judge? 
Me: Yes, that's the question. 
Them: So my— so I'm asking you. 
Me: Oh. 
Them: I'm being a dick now. I'm asking you, like, I'm trying to— now I'm basically— I'll tell you why I'm asking you. 
Me: Oh. 
Them: So one of the techniques I use for teaching people things is like I evoke an emotion. So I'm going to ask you like a hard question that I know that it's unlikely you have the answer and now you're not going to forget the answer, I hope. 
Me: Okay, go for it. Go for it. 
Them: So, so no, what is the answer? Try to guess it. Try to guess it. I did this to Natalia in my, in my, in my, not my call, but in the presentation I gave to her. And apparently she really liked that. Ask me a question, asking, and I told her, well, what do you think is the answer? 
Me: Oh. Yeah. Huh. Yeah. 
Them: And then she answered it and she put it and I was like, okay, this is the answer. And then she was really happy about it. 
Me: Yeah, I think my guess is that I would— let me just join from my phone real quick. I'm walking over. Let me just join real quick. One second.
