function [X,P,G] = cgdfp4(A,b,it,T) %#codegen
	d = size(A,2);
	X = cast(zeros(d,it),'like',T);
	P = cast(zeros(d,it),'like',T);
	G = cast(zeros(d,it),'like',T);
	x = cast(zeros(d,1),'like',T);
	p = cast(zeros(d,1),'like',T);
	g = cast(zeros(d,1),'like',T);
	pA = cast(zeros(1,d),'like',T);
	gdq = cast(zeros(d,1),'like',T);
	etap = cast(zeros(d,1),'like',T);
	Ax = cast(zeros(d,1),'like',T);
	gdeta = cast(zeros(d,1),'like',T);
	gammap = cast(zeros(d,1),'like',T);
	q = cast(0,'like',T);
	eta = cast(0,'like',T);
	gamma = cast(0,'like',T);
	Ax(:) = A*x;
	p(:) = Ax - b;
	g(:) = p;
	for i = 1:it
		display(sprintf('===== Iteration: %d =====',i));
		%%%
		pA(:) = p'*A;
		q(:) = pA*p;    
		%%% q = <p,Ap>
		gdq(:) = g/q;
		eta(:) = gdq'*g;
		%%% eta = <g,g> / <p,Ap>
		etap(:) = eta*p;
		x(:) = x - etap;
		%%% x = x - eta*p
		Ax(:) = A*x;
		g(:) = Ax - b;
		%%%
		gdeta(:) = g/eta;
		gdq(:) = g/q;
		gamma(:) = gdeta'*gdq;
		%%% gamma = <g,g> / eta * q
		%%% (here eta = <g_old, g_old> / <p, Ap> and q = <p, Ap>)
		gammap(:) = gamma*p;
		p(:) = g + gammap;
		%%% p = g + p * <g,g> / eta * q
		X(:,i) = x;
		P(:,i) = p;
		G(:,i) = g;
	end;

