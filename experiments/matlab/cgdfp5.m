function [X,P,G] = cgdfp5(A,b,it,T) %#codegen
	d = size(A,2);
	X = cast(zeros(d,it),'like',T);
	P = cast(zeros(d,it),'like',T);
	G = cast(zeros(d,it),'like',T);

	x = cast(zeros(d,1),'like',T);
	Ax = cast(zeros(d,1),'like',T);
	p = cast(zeros(d,1),'like',T);
	gammap = cast(zeros(d,1),'like',T);
	g = cast(zeros(d,1),'like',T);
	pscl = cast(zeros(d,1),'like',T);
	pA = cast(zeros(1,d),'like',T);
	etapscl = cast(zeros(d,1),'like',T);
	gdq = cast(zeros(d,1),'like',T);
	etap = cast(zeros(d,1),'like',T);
	gdeta = cast(zeros(d,1),'like',T);
	ng = cast(0,'like',T);
	ngnew = cast(0,'like',T);
	q = cast(0,'like',T);
	eta = cast(0,'like',T);
	gamma = cast(0,'like',T);

	Ax(:) = A*x;
	p(:) = Ax - b;
	g(:) = p;
	ng(:) = g'*g;
	for i = 1:it
		display(sprintf('===== Iteration: %d =====',i));
		%%%
		pscl(:) = p*d;
		pA(:) = p'*A;
		q(:) = pA*pscl;    
		%%% q = d <p, Ap>
		%%% this q is scaled by d
		eta(:) = ng/q;
		%%% eta = <g,g> / d <p,Ap>
		etapscl(:) = eta*pscl;
		x(:) = x - etapscl;
		%%% x = x - eta*p (the d in pscl cancels here)
		Ax(:) = A*x;
		g(:) = Ax - b;
		%%%
		ngnew(:) = g'*g;
		gamma(:) = ngnew/ng;
		%%% gamma = <g,g> / <g_old,g_old>
		gammap(:) = gamma*p;
		p(:) = g + gammap;
		%%% p = g + p * <g,g> / <g_old,g_old>
		ng(:) = ngnew;
		X(:,i) = x;
		P(:,i) = p;
		G(:,i) = g;
	end;

