Veribench RL Envs Subproject - October 05
VIEW RECORDING - 33 mins (No highlights): https://fathom.video/share/shYxvveG4FDZSdB145yXiw4JqjNsLrnu

---

0:00 - Brando Miranda (brandojazz@gmail.com)
  Can you guys hear me, I can hear someone, yes, this is Ethan, yes Ethan I can hear you, hey Brando, yeah I can hear you guys now, what's up, hey guys can you accept my invite please, so that I don't have to redo this, I'm guessing this is about github, yeah cool, Brando did you, the link gives me, the link that you sent is like 404, did you invite my github, yeah it says, it's the one with the teddy bear glasses, no, yeah I don't see,
  ACTION ITEM: Resend GitHub invites to Emily, Varun, Ethan R Lee, Ethan L - WATCH: https://fathom.video/share/shYxvveG4FDZSdB145yXiw4JqjNsLrnu?timestamp=57.9999

1:00 - Emily Xia
  I the invitation anywhere. Oh, never mind. I didn't see it. Yeah, it's either notifications or from your email, and then you can log into it.

1:08 - Varun Madan
  try resending it? Sure.

1:11 - Emily Xia
  Why do people have such weird- Sorry.

1:27 - Brando Miranda (brandojazz@gmail.com)
  Everyone has like a weird- Can you send it again here? Oh yeah, my username is this.

1:40 - Emily Xia
  You have mine, so it's okay.

1:46 - Varun Madan
  Okay, cool. Yeah, I guess I can get us started, guys.

1:52 - Emily Xia
  I can kind of just introduce a little bit about what we're doing, why we're gathered here, and then we can take it from there.

1:59 - Varun Madan
  Does that sound good? Are guys? Mm-hmm. Yes. Sounds great. Cool.

2:03 - Brando Miranda (brandojazz@gmail.com)
  Let's get started.

2:04 - Varun Madan
  So, yeah, I've talked to all of you guys individually now about, like, our project, our meta project that we're working on, which is predictably, like, you know, predictably scaling, like, post-training processes, specifically RL, right?  And I think that's, like, the biggest thing that we're trying to go after. And inside of that, you guys all have a little bit of experience with VeriBench, right?  So I guess one of the biggest, like, aha moments was what if we try improving, like, predicting the right environments that improve performance on VeriBench the most, right?  That's a domain that you guys all know pretty well. It's a good starting point to get into this, like, bigger project anyway because it's, like, utilizing your strengths and also, like, getting familiar with, like, running, like, large-scale RL jobs, like, at scale.  So I think that's really important. And, obviously, connects well. to Brando's thesis as well, so everybody's interests are aligned in this thing, so that's pretty good, this is going to be a subproject under our large open source project, and yeah, so this is a pretty cool undertaking, Brando started a little bit on it, basically we're trying to see, is this transferable to a VeriBench domain, it's slightly different, Brando can get into the nitty gritties of why this is different from our initial paper, but yeah, I just wanted to get us started.  Yeah, awesome, yeah, is there anything you want to save Varun, because otherwise I think we can just start discussing like ideas and things like that we can start doing.  I'll let you lead this subproject. Awesome, awesome, yeah, so let's see, so what do I have to say?

3:48 - Ethan R Lee
  Yes, wait, one second, one second, Ethan has a question.

3:52 - Varun Madan
  Ethan, go ahead.

3:53 - Ethan R Lee
  like, I was wondering, you mentioned like a previous project that this is being based on, like, should I read that, and where can I find that?  Thank Yeah, you should read that. Yeah, it's the paper that Brando sent you. Oh, okay. So that's like predicting the skin.

4:08 - Varun Madan
  Yeah, maybe what I can do, so since that project is private, we probably want to reuse some of the code and the paper as it gets updated.

4:15 - Brando Miranda (brandojazz@gmail.com)
  I'm going to make a git some module for that in this repo and let me know, guys, if you guys can see it.
  ACTION ITEM: Add private-repo module to current repo; notify team - WATCH: https://fathom.video/share/shYxvveG4FDZSdB145yXiw4JqjNsLrnu?timestamp=261.9999  That way we don't have to harass Varun with adding people to another project because that's really annoying. Wait, actually, no, no, no, no, no.

4:32 - Varun Madan
  So this is actually something I've reasoned about. Our infrastructure right there is like, it's very specialized for that specific mathematical domain.  I would like, I will create a special module that I will add to this repo in like a couple of minutes, mainly because there are only certain things that I want to transfer to this project.  I want it to be like actually open, mainly because obviously the infrastructure is pretty similar. Like what we're going to do is we're going to use.  I NEMO RL, which is basically, it's the RL framework of NVIDIA, and it allows us to like change models pretty interchangeably, you can define your reward functions on there, it's very customizable, it's I think, in my opinion, better than Verl, so we're using that, that's like the only big infrastructure thing that we need, and like that's not even an infrastructure thing.  The best part about mathematics is, environments are literally like, they don't matter on the infraside as much as like terminal coding and stuff, so I will say that like, I think it's advisable to just start off from NEMO RL, and I think that's where we should build off of.  Perfect, well that's why we have this meeting, so that we can start doing things.

5:44 - Brando Miranda (brandojazz@gmail.com)
  Give me one second. What are you up to?

5:50 - Varun Madan
  I am opening something, give me one second. Okay. Okay.

5:58 - Brando Miranda (brandojazz@gmail.com)
  Okay. So. Okay. Oh, okay. So let's see. Okay. Do we have like a, well, the way I, yeah, I don't.  Okay. So let me open my, let me just share my screen. Can you guys see it? Yeah, I can see your screen.  Yeah. Awesome. So let me see what I'm going to do is open that project, that GitHub repo in, in my cursor and, um, basically write some notes so that we can RL or I don't understand.
  ACTION ITEM: Upload RL paper PDF to current repo - WATCH: https://fathom.video/share/shYxvveG4FDZSdB145yXiw4JqjNsLrnu?timestamp=409.9999  This always moves, like why, like what we can start with, sounds good, so that I don't have to repeat things, we can have a meetings folder here, that's okay, meetings, file October 5, 2026.md, oh my god, this is not nice, okay, so, okay, so I think the main thing to, okay, so let me see what, Varun can always correct me if he needs to jump in, but, like, I think the main goal would be to show that the method from the paper, I'll put the path here, in a second, put path to PDF in this repo,  So the main goal is for the method, the predictive method from that paper to show that it generalizes to solving or creating other environments that solve benchmarks.  Is that like a good way to say it, Varun, or how do you say it? Or is that good enough?

8:21 - Varun Madan
  So showing the method from the paper, I think we like, I think we just want to be more specific.  We want it to generalize on VariBench, right? I think we should be very goal defined on that. So on VariBench specifically?

8:35 - Brando Miranda (brandojazz@gmail.com)
  Yes, on VariBench.

8:37 - Varun Madan
  And then, and not only just generalizing to that, but it's like predicting the optimal environments for VariBench, right? And if there's any slight variation or deviation of the law that needs to be done, that's fine as well, as long as it's tested well.  So I would just say that qualification is really important because we have to be very specific about what we want.  Yeah, so do we call it a law?

9:04 - Brando Miranda (brandojazz@gmail.com)
  I remember that you didn't like that term, so I'm just wondering. Let's just say scaling relationship for now.

9:09 - Varun Madan
  I think as we get more data, we can define it into a law, but a law has to be tested so many times that if we call it a law right now, every single reviewer around the world is going to start grilling us.

9:20 - Ethan R Lee
  So I intentionally avoid that scrutiny. Awesome. Awesome. Sounds good.

9:25 - Brando Miranda (brandojazz@gmail.com)
  So let me just write what the goal of VariBench is and remind, because VariBench is changing, honestly, like every day.  So let me tell you what is the current state and what I think people can contribute and how I am thinking to do experiments and things.  So before I write anything, if you can see, if you've worked with me before, you may be familiar with my, in the main repo, I have like this experiment folder and I write all the experiments.  And all the code, like all the code prompts and things are here. And as they succeed, I move them to the main source if needed or.  Just ignore it and just put it in the paper. But what I'm thinking is that I could probably spend a few hours every day thinking about what has to be done and creating tasks and prompts and things like that.  And maybe I can get some help finishing them or doing them with me. Something like that is like maybe the first week is what we can do.  And as you guys get more familiar with it, you can get more independence on doing something significant. Does that sound like a good first week?  Yeah. And you guys can comment at any point. And I see everyone's muted. So like, you know, if you don't say anything, I won't know if you have an opinion, just so you know.  So for VariBench, the main task is to, so the main task is to, or the main capability is to solve code verification of the
  ACTION ITEM: Send VariBench paper PDF to Emily - WATCH: https://fathom.video/share/shYxvveG4FDZSdB145yXiw4JqjNsLrnu?timestamp=664.9999  The original code, as you guys know. So for that, I created this like SCSC metric. So this like, okay, maybe Emily's not familiar with this, right, Emily?  Oh yeah, I don't think, I'm not that familiar.

11:14 - Emily Xia
  That's fine.

11:15 - Brando Miranda (brandojazz@gmail.com)
  So like for you, Emily, you can, I'll just go through it quickly now, but I'll send you the paper to do read the revenge paper recent.  So task for Brando, send most recent PDF. But the idea is that, yeah, so the, so to solve the task, so the task is basically solve code verification of the original code.  So usually we have, in this setting, we have some Python code that is already, that already exists, and we auto formalize it to lean for, and then  Goal, so very much V1, defined this as just an auto-formalization task. So we just translated it to Python, translated Python to Lean, and made sure that the Lean was similar to the Goal to Lean file via some metric that I'm defining below here that I haven't written yet.  And this is like a star. And as long as this checked past well, we were happy. That's very bench V1, and I think very bench V2, which is what Ethan has done more, is we auto-formalize, but we also, actually, it requires a different picture.  We connect the original code to the Python, to the Python code to the Lean code, so we auto-formalize plus connect the two.  And the two ways we have to connect these things, as far as I know, is... in clip. Let's If see Thank  With differential testing, basically having shared tests between the Python and the Lean that say that the two are equivalent, or something that Ethan came up with, or we came up with, I think Ethan came up more with it, so I'll give him more credit, but the idea is, is the name that we, well, I like to call it Prover Differential Testing, is that the name you came up with, that we concluded?  Yeah, something like Proving Testing, or something.

13:31 - Ethan R Lee
  Okay, we need to figure out a name, and choose it, and stick with it, so that we can, like, people know what we're talking about, you know?

13:39 - Brando Miranda (brandojazz@gmail.com)
  So for now, I'm going to call it, like PT. Prover Differential Testing is the name for right now. Yeah, check it out.  We use Differential Proving. Oh, Differential Proving. Okay, that's better. Differential Proving. Differential Differential Differential Proving. Proving.

13:58 - Ethan R Lee
  Proving. Differential Oh, oh, okay.

14:03 - Brando Miranda (brandojazz@gmail.com)
  DP. Oh, no, but that's like dynamic programming. Okay, whatever. It's fine. I think this name is good. So the idea is that instead of having, so this one differential testing, by the way, AI people don't know what differential testing is.  So in the paper, we need to define it. And Ethan, if you saw my feedback, but in this paper, we probably need to define it too.  But differential testing is approximately shared unit tests, shared tests, because it can be unit test or property based testing.  So AI people also don't know what property based testing is. So we need to define that. So everyone here has to like, I'll send the, hopefully the AI bot will send you the meeting recording.  And if it doesn't let me know, and then you can like Google or make notes right now on what terms you need to know.  So basically property based testing is just like unit test, but with respect to a property. So if it tests like reflexivity for addition or.  Or transitivity or whatever. So properties, properties for with many tests. Like a unit test is like a single test.  Like a single little test. That's why it's called a unit test. And I guess Rakshit did more VariBench V3, although we didn't have a paper for it, but it was like a multi-repo VariBench, which we called VariBench Depths.  So for now, think because this one proved to be much, we de-risked that this project is much harder than we expected.  So for now we probably will avoid it unless I engage directly to it. Because I think like it requires, it's so, like Rakshit, think it's like pretty difficult.
  ACTION ITEM: Type up VariBench Depths simplification; send to Brando + Rakshit - WATCH: https://fathom.video/share/shYxvveG4FDZSdB145yXiw4JqjNsLrnu?timestamp=951.9999  requires like a full-time, and Ethan, right? It requires like full-time attention to it.

15:55 - Ethan R Lee
  And I think like, I came up with like some kind of way to think about it. might simplify a bit.  I mean, I can type it up.

16:03 - Brando Miranda (brandojazz@gmail.com)
  It's very short, but I guess we can discuss that later anyway. Yeah, I think the best way to address that actually is to type it up and send it to me and Rakshit in a separate chat to not spam Emily and Varun.  Send that. And yeah, any questions? free to spam us, by the way. Feel free to Spam them. is more context.  Spam them if they want. Spam them if they want. don't mind. Yes, please. Okay, so I guess my first question is like, which version of VariBench are we going to be working on for this project?

16:40 - Ethan R Lee
  These two. So we're going to do VB1 and VB2.

16:45 - Brando Miranda (brandojazz@gmail.com)
  Okay, like VB2 has a lot of different sort of metrics and stuff.

16:50 - Ethan R Lee
  So I think it will help to get really familiar with what each of them are testing. Yeah, it's a bit complex, but I think it's...  complex It's worth it. VB1 also can be done. I think it, like, abstracts away a lot of the stuff, like, very strong source to lean translation verification.  I guess my main concern for VB1 is, like, aren't most of the tasks, like, saturated by now? No, doesn't matter because that's only for frontier models.

17:24 - Brando Miranda (brandojazz@gmail.com)
  We're not going to train frontier models. We're going to train, like, Quen 7 billion or whatever Varun recommends. Like, he's the expert on which type of model we'll train.  And if those are saturated, then we'll just create VariBench V1.1 so that we have something to do. I see.  That makes sense. My question is, where are you Ben3 models right now? Oh, sorry. Quick comment. yes, we can start with VariBench because it's something we can put on my thesis, but if we find that it's saturated or something like that, we can always use other Bench.  That's not the main goal of the project. I can figure out a way to include it in my thesis.  Very much V2 also has a lot of tasks that I curated.

18:12 - Ethan R Lee
  Well, I am mostly Codex. But they are strong enough to the point that Astra cannot saturate them with a token limit.  Sorry, Varun, you were saying something?

18:23 - Varun Madan
  Yeah, so I was saying that the models that we used for the mathematics project, well, the first initial pilot was 1.74B and 8B, predicting a 14B model.  So we were using all of the QUEN3 sizes, and it was the same fine tuning warmup that taught it basic math and coding skills just to get it started for RL.  So that was our configuration. So I think something like that could be cool here just to keep it controlled.
  ACTION ITEM: Share Quen3 warm-start weights w/ Brando; then Brando runs 8-rollout eval (1.7/4/8B) - WATCH: https://fathom.video/share/shYxvveG4FDZSdB145yXiw4JqjNsLrnu?timestamp=1138.9999  Yeah, yeah, of course. if you actually have...

19:00 - Brando Miranda (brandojazz@gmail.com)
  Is initial code that you can just push? Like, that might be useful so that we can save time? Yeah, of course.  when you have time, just push it and let us know?

19:09 - Varun Madan
  Yeah, I'll just give you the weights to the fine-tuned warm start so that you can just start RLing on it.  Oh, that's even better, probably.

19:17 - Brando Miranda (brandojazz@gmail.com)
  Probably even better. I don't know if we need to warm up to Lean, because Lean is different from natural language math.  Oh, okay.

19:31 - Varun Madan
  Yeah, that's fine. is a programming language.

19:38 - Brando Miranda (brandojazz@gmail.com)
  Yes, but my curiosity is, is Quen3 trained on Lean?

19:43 - Varun Madan
  Oh, probably, yeah.

19:46 - Brando Miranda (brandojazz@gmail.com)
  Probably.

19:46 - Varun Madan
  Okay, if it is trained on Lean and it performs decently, then we can skip the SFT warm start.

19:51 - Brando Miranda (brandojazz@gmail.com)
  So, de-risking, I can do this for us, de-risking BM on Rona and Ival on... Um... QAN 3, right? Yeah, QAN 3, start with 1.7B, 4B, and 8B.  Say it again, 7, what? 1.7, 4, and 8B.

20:14 - Varun Madan
  Okay. And, like, basically 1.7 is the most important because if it's too hard for 1.7, then we have to reevaluate.  And basically what we want to do is, like, run 8 rollouts, right? G equals 8. And then C, does it pass, like, more than 0 out of 8 times?  And, like, is it not 8 out of 8? Like, it should be in the middle. And if it's within the normal distribution, that's a good thing for RL.  So I think that's the first de-risking that you have to do. Perfect, perfect. I can start that and send it.

20:43 - Brando Miranda (brandojazz@gmail.com)
  And maybe Ethan, Emily, or Rakshit, or all three can...

20:48 - Varun Madan
  I'll do a PR and you can help me check it, guys.

20:50 - Brando Miranda (brandojazz@gmail.com)
  And remember, remember, we're using...

20:54 - Varun Madan
  We started the SFT Warm Start with Quen 3 Bass, and then... And from the base model, we had to do some SFT warmup.  So that's why I used warmup because in the base model, it's not post-trained on anything. And we do this intentionally because different sizes are post-trained in different ways in Quen, right?  So that's why they're different. So it's important to de-risk that, see if it understands on the base model. Yeah, I'll do this on the base model and see how it does.

21:26 - Brando Miranda (brandojazz@gmail.com)
  On the base model. Don't worry. Or the instruction when they release, if that's okay. Yes or no? No, I don't recommend the instruction fine-tuned one.

21:37 - Varun Madan
  Because the instruction fine-tuned one is instruction fine-tuned in different ways. So it's not completely controlled. I've done this experiment.  I understand. I understand.

21:46 - Brando Miranda (brandojazz@gmail.com)
  Got it. Got it. Fine.

21:47 - Varun Madan
  So just evaluate it, see if it's able to pass, and then we'll see.

21:51 - Brando Miranda (brandojazz@gmail.com)
  Understood. So guys, just a quick comment. Today I can make an exception and stay there five more minutes. But we should start on time because it's hard.

22:03 - Varun Madan
  We can stay five more minutes today, because the other meeting, Andrew's not even here for it, so it'll be chiller, so we're fine.

22:12 - Brando Miranda (brandojazz@gmail.com)
  Yeah, but I think I probably have to go at like 25 minutes for all my meetings, otherwise I can't do the next thing.  Yeah, okay. Anyways, let me continue. The next thing is sort of important. So this is like the benchmarks. So this is like the data.  And now I guess like what I want to start is like the metrics for VariBench. So the metric I made up for VariBench V1, so for VariBench V1, I like the V after here.  So the metric for VariBench V1 is something that I call the smooth conjunctive, smooth conjunct... Smooth conjunctive score for code verification.  Like, maybe we can rename it if we want, but for now, this is the name. We can brainstorm that offline.  But what it really is, is it comes from, I'm going to say it verbally and then write the equation.  It comes from the idea that if you think about what does code verification mean? When you create a benchmark, you're basically defining what the task is with the data and with the metrics.  So I was thinking, what does it mean to do code verification? And what I sort of concluded was that, well, your implementation has to pass its own test.  It has to write the right formal specifications. And this is actually sort of an important nuance. Formal specification means unproven theorems.  So you need to write like the right theorems. And third, prove them. So all those three things. So basically.  basically. You just do a, so the ideal metric would be an, like, so I guess like the ideal metric, so maybe we can call it the ideal SESC, can be, the ideal SESC can be, would be sort of like internal consistency of the code with the tests, and internal consistency with the proofs, and the formal theorem, formal spec coverage.  Like it has to fully cover all the, all the formal specs. Does that make sense? What, what the ideal one is?  So, because this is like very, very harsh, in the sense that it has like, like the mirage paper effect, because of the end, I sort of like changed it to a product, because products are like more, more nicer, behaved, and these are actually means, that also helps to make it smoother.  And last but not least, if you just multiply numbers that are like bounded between zero and one, they just get smaller.  So to avoid that dumb issue, you just take the geometric mean, like in this case, one third, right? The one third basically just says the geometric mean with one third says the average end of these three.  So far, so good.

25:25 - Ethan L
  Wait, one second. I was actually kind of confused why you did this in the V1. Because like, if you have like wrong specifications, it's very easy to prove like something that's not correct about the original code.  And I think like when we submitted to a workshop, like a lot of reviewers had issues with this being kind of arbitrary.  Yeah, we can, we can, this requires a longer discussion.

25:51 - Brando Miranda (brandojazz@gmail.com)
  We can have a, maybe we can have a separate meeting about that tomorrow or another day. For now, or send me an easy question.  can try to clarify. Because it has to be clear to you and the reviewers what the definitions are, and there's like many definitions, and yes, it's arbitrary, that's why I was hoping we can have time to discuss this, so before I continue, Varun, do we have five more minutes for this meeting, or what should we do, who's meeting for our next meeting?  Sure, yes, we have five more minutes. The other meeting, do people, okay, so it's only you and me meeting for the next meeting?

26:27 - Varun Madan
  Shree as well, and Ilya, so don't worry about it, five minutes, we can definitely spend more here. Yeah, just let them know so that they don't remain waiting.

26:36 - Brando Miranda (brandojazz@gmail.com)
  Yeah, I already let them know. Okay, maybe I can engage real quick with the question. So, for this metric, I just want to point out like some properties about it, like Ethan asked a question.  So, so imagine that the model is solving like the. Task of, so for example, so like transforming like myad.python to myad.lean, so there's like a definition of addition in both of them, so like a test in both of them would look like 1 plus 1 equals 2 with the Python syntax, and then it would look like 1 plus 1 equals 2 with like this lean syntax, and there will be multiple tests, and if there's like 10 tests, then the score, and it passes 8 of them, then this guy for that data point, for that data point would be like, say it passes like 8 out of 10, so it would be 0.8, right?  Real quick, 8 out of is like the DT, right? There's no DT right now, it's very bench V1. Okay, wait.  Sorry, I'm on my phone, I can't already see.

28:02 - Ethan L
  So Veribenge V1 is just evaluating if the models can auto-formalize, i.e.

28:06 - Brando Miranda (brandojazz@gmail.com)
  auto-formalization is just literally defined as translation. It's just translating. Can you translate it into lean? Okay, wait, what are the 10 then?  Like, what is... Say that there are 10 tests, like 0 plus 1 plus 1, 1 plus 2, 1 plus 3, all the way to 1 plus 10.  Then this is sort of like a DT, is it not?

28:32 - Ethan L
  No, there's no DT, because there's just like the...

28:37 - Brando Miranda (brandojazz@gmail.com)
  The task the model is asked to do is, given this Python task in Veribenge V1, it only measures its ability to auto-formalize, not to verify the original code.  So it's only, can you transform this code into lean? And does that code work? It's like what we're trying to define.  Okay, I'm a bit confused, but I'll... Look at the original paper a bit closer, then.

29:02 - Ethan L
  Well, what are you confused about? Because I think, I thought, like, that was what we meant by DT, like, testing if the outputs on various inputs are the same thing.

29:12 - Brando Miranda (brandojazz@gmail.com)
  So in DT, we enforce that the, so, like, when you translate a Python file to a Lean file, if you don't, if you don't have, if you do a shared set of unit tests, then the data structure has to be shared, or has to, like, there's some similarity that, okay, so if you don't, if you completely ignore the difference, then in theory, the Lean file could be any arbitrary, like, the space of programs is much, much, much larger, and it's true, in the DT project, we try to solve to some degree that, I don't know if we have a mathematical proof that we guarantee that we always solve it and  That in the other case, it never happens. So that's the difference. Okay, cool. this requires like a Python lean adapter or whatever, right?

30:10 - Ethan L
  No, and the VVB1 does not require a lean adapter.

30:14 - Brando Miranda (brandojazz@gmail.com)
  Like the model is just like rogue and they can just write whatever code it wants. Right, right.

30:20 - Ethan L
  But like, now that you're comparing like 1 plus 1 is 2 in Python and 1 plus 1 is 2 in lean.  Like, how do you know the Python 2 is the same as lean 2? Are we using LLM judgments? You don't.  You're not comparing them.

30:32 - Brando Miranda (brandojazz@gmail.com)
  You're not trying to show it. You're just trying to make sure the formal model works, but you're not trying to say for sure it's the formal model of the original code.  Just like when you write math and you write lean and you don't, there's no way to connect the lean code you wrote to like the paper and hand the paper, the math you wrote by paper, you know?  Right, exactly. It's just the ability to translate. the process So, Thank

31:01 - Ethan L
  Okay, like, what would it look like if it failed one of those 10 tests?

31:06 - Brando Miranda (brandojazz@gmail.com)
  Like, the python files never fail, or, okay, like, the, the, the, well, it would just, I don't know how to answer that except that it would just fail.  Like, would it say, like, 1 plus 1 is 3, or?

31:24 - Ethan L
  Yeah, it would just not type check and lean, yeah, for whatever reason. Okay, well, uh, I'm kind of confused, like, how does it not type check on only some of the tests?

31:39 - Brando Miranda (brandojazz@gmail.com)
  Like, so, okay, so, like, okay, um, we are out of time, but we can discuss this async, but, um, this is what I, what I, what I want you guys to do.  I'll send you the very bench paper and make sure that it's, you have, if you have questions, just send them async and I'll engage.  Sounds good? Yeah, sounds good. The main goal is that we can, and I'll send, and Varun will send the most recent version of the RL paper PDF.
  ACTION ITEM: Create and assign tasks/PRs to team; then team reviews Varun's eval PR - WATCH: https://fathom.video/share/shYxvveG4FDZSdB145yXiw4JqjNsLrnu?timestamp=1930.9999  And can you push it to the prod, to this repo, Varun? And yeah, that's all for today. I'll send tasks and PRs for people to engage with async.  Emily, Rakshit, Ethan, is that, sounds good? Right, sounds good. Sounds good. Awesome. See you guys. Alright, thanks all. see ya.  Bye. Thank you.