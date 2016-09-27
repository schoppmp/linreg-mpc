function [X,P,G] = cgdfp8(A,b,it,T) %#codegen
	d = size(A,2);

	TT = numerictype(T);
	%TT.Signedness = 'SIGNED';

	X = cast(zeros(d,it),'like',T);
	P = cast(zeros(d,it),'like',T);
	G = cast(zeros(d,it),'like',T);

	x = cast(zeros(d,1),'like',T);
	Ax = cast(zeros(d,1),'like',T);
	p = cast(zeros(d,1),'like',T);
	gammap = cast(zeros(d,1),'like',T);
	g = cast(zeros(d,1),'like',T);
	gscl = cast(zeros(d,1),'like',T);
	%pscl = cast(zeros(d,1),'like',T);
	pA = cast(zeros(1,d),'like',T);
	%gdq = cast(zeros(d,1),'like',T);
	etap = cast(zeros(d,1),'like',T);
	etaAp = cast(zeros(d,1),'like',T);
	%gdeta = cast(zeros(d,1),'like',T);
	ng = cast(0,'like',T);
	%ngnew = cast(0,'like',T);
	gp = cast(0,'like',T);
	gAp = cast(0,'like',T);
	q = cast(0,'like',T);
	eta = cast(0,'like',T);
	gamma = cast(0,'like',T);

	Ax(:) = A*x;
	g(:) = Ax - b;
	ng(:) = max(abs(g));
	%ng(:) = 1.0;
	%gscl(:) = g/ng;
	gscl(:) = mydivide(TT,g,ng);
	%gscl(:) = g;
	p(:) = gscl;
	for i = 1:it
		display(sprintf('===== Iteration: %d =====',i));
		%%%
		pA(:) = p'*A;
		q(:) = pA*p;    
		%%% q = <p, Ap>
		gp(:) = g'*p;
		%eta(:) = gp/q;
		eta(:) = mydivide(TT,gp,q);
		%%% eta = <g,p> / <p,Ap>
		etap(:) = eta*p;
		x(:) = x - etap;
		%%% x = x - eta*p
		%Ax(:) = A*x;
		%g(:) = Ax - b;
		etaAp(:) = eta*(pA)';
		g(:) = g - etaAp;
		ng(:) = max(abs(g));
		%ng(:) = 1.0;
		%gscl(:) = g/ng;
		gscl(:) = mydivide(TT,g,ng);
		%gscl(:) = g;
		%%%
		gAp(:) = pA*gscl;
		%gamma(:) = gAp/q;
		gamma(:) = mydivide(TT,gAp,q);
		%%% gamma = <g,Ap> / q
		%%% (here eta = <g_old, g_old> / <p, Ap> and q = <p, Ap>)
		gammap(:) = gamma*p;
		p(:) = gscl - gammap;
		%%% p = g + p * <g,g> / eta * q
		display(sprintf('q=%.6e e=%.6e g=%.6e ng=%.6e gscl=%.6e np=%.6e ng=%.6e',double(q),double(eta),double(gamma),double(ng),norm(double(gscl))^2,norm(double(p))^2,norm(double(g))^2));
		X(:,i) = x;
		P(:,i) = p;
		G(:,i) = g;
	end;

